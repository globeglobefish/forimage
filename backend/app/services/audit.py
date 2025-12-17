"""
Image Audit Service - Async Background Processing
图片内容审核服务 - 异步后台处理模式

支持的审核服务商：
1. 阿里云内容安全 (aliyun)
2. 腾讯云数据万象图片审核 (tencent)

设计原则：
1. 不阻塞用户上传 - 图片先保存为 pending 状态
2. 后台异步审核 - 使用 BackgroundTasks
3. 审核完成后更新状态 - approved 或 rejected
4. 任何异常都不应该影响主进程
5. API错误时图片保持pending状态，不误封
"""
import io
import logging
import json
import asyncio
import base64
import hashlib
import hmac
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Tuple
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import httpx

logger = logging.getLogger(__name__)

# 全局线程池，限制并发数，避免资源耗尽
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="audit_")

# 审核超时时间（秒）
AUDIT_TIMEOUT = 30

# 重试配置
MAX_RETRY_ATTEMPTS = 3  # 最大重试次数
INITIAL_DELAY = 2  # 首次审核前的初始延迟（秒）
RETRY_DELAYS = [3, 5, 10]  # 每次重试前的延迟（秒），指数退避


class ImageAuditService:
    """图片内容审核服务"""
    
    def __init__(
        self, 
        enabled: bool, 
        provider: str, 
        api_key: str, 
        api_secret: str, 
        auto_reject: bool,
        tencent_bucket: str = "",
        tencent_region: str = ""
    ):
        self.enabled = enabled
        self.provider = provider
        self.api_key = api_key
        self.api_secret = api_secret
        self.auto_reject = auto_reject
        # 腾讯云特有配置
        self.tencent_bucket = tencent_bucket  # 格式: bucket-appid
        self.tencent_region = tencent_region  # 如: ap-guangzhou
    
    def audit_image_sync(self, image_bytes: bytes, image_url: str = None) -> Tuple[bool, str, dict]:
        """
        同步审核图片 - 在线程池中执行
        Returns: (is_safe, suggestion, details_dict)
        
        is_safe=True: 图片安全，可以通过
        is_safe=False: 图片不安全，需要拒绝
        suggestion: pass/block/review/error/skip
        
        Args:
            image_bytes: 图片二进制数据
            image_url: 图片公网URL（腾讯云审核时使用）
        """
        # 前置检查 - 快速返回
        if not self.enabled:
            return True, "skip", {"status": "audit_disabled"}
        
        if not self.provider or self.provider not in ("aliyun", "tencent"):
            return True, "skip", {"status": "unsupported_provider", "provider": self.provider}
        
        if not self.api_key or not self.api_secret:
            return True, "skip", {"status": "no_credentials"}
        
        if not image_bytes or len(image_bytes) == 0:
            return True, "skip", {"status": "empty_image"}
        
        try:
            if self.provider == "aliyun":
                return self._call_aliyun_api(image_bytes)
            elif self.provider == "tencent":
                return self._call_tencent_api(image_bytes, image_url)
            else:
                return True, "skip", {"status": "unsupported_provider"}
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Audit API error: {error_msg}")
            # API错误时，返回安全+error，让图片保持pending
            return True, "error", {"status": "api_error", "message": error_msg[:500]}
    
    def _call_aliyun_api(self, image_bytes: bytes) -> Tuple[bool, str, dict]:
        """调用阿里云内容审核 API"""
        # 动态导入，避免启动时报错
        try:
            from alibabacloud_imageaudit20191230.client import Client
            from alibabacloud_imageaudit20191230.models import (
                ScanImageAdvanceRequest,
                ScanImageAdvanceRequestTask,
            )
            from alibabacloud_tea_openapi.models import Config
            from alibabacloud_tea_util.models import RuntimeOptions
        except ImportError as e:
            logger.warning(f"Aliyun SDK not installed: {e}")
            return True, "skip", {"status": "sdk_not_installed"}
        
        config = Config(
            access_key_id=self.api_key,
            access_key_secret=self.api_secret,
            endpoint='imageaudit.cn-shanghai.aliyuncs.com',
            region_id='cn-shanghai'
        )
        
        client = Client(config)
        
        runtime = RuntimeOptions()
        runtime.connect_timeout = 10000   # 10秒连接超时
        runtime.read_timeout = 20000      # 20秒读取超时
        runtime.autoretry = False         # 禁用自动重试，避免长时间阻塞
        
        task = ScanImageAdvanceRequestTask()
        task.image_urlobject = io.BytesIO(image_bytes)
        
        request = ScanImageAdvanceRequest(
            task=[task], 
            scene=['porn', 'terrorism']
        )
        
        response = client.scan_image_advance(request, runtime)
        
        if not response or not response.body:
            logger.warning("Empty response from audit API")
            return True, "error", {"status": "empty_response"}
        
        result = response.body.to_map() if hasattr(response.body, 'to_map') else {}
        
        # 解析结果
        data = result.get('Data', {})
        task_results = data.get('Results', [])
        
        if not task_results:
            logger.warning("No audit results returned")
            return True, "error", {"status": "no_results"}
        
        sub_results = task_results[0].get('SubResults', [])
        
        overall_suggestion = 'pass'
        flagged_scenes = []
        
        for sub in sub_results:
            suggestion = sub.get('Suggestion', 'pass')
            if suggestion == 'block':
                overall_suggestion = 'block'
                flagged_scenes.append({
                    'scene': sub.get('Scene', ''),
                    'label': sub.get('Label', ''),
                    'rate': sub.get('Rate', 0)
                })
            elif suggestion == 'review' and overall_suggestion != 'block':
                overall_suggestion = 'review'
                flagged_scenes.append({
                    'scene': sub.get('Scene', ''),
                    'label': sub.get('Label', ''),
                    'rate': sub.get('Rate', 0)
                })
        
        # 只有明确的 block 才拒绝
        # review 根据 auto_reject 设置决定
        is_safe = overall_suggestion == 'pass'
        if self.auto_reject and overall_suggestion == 'review':
            is_safe = False
        
        return is_safe, overall_suggestion, {
            'provider': 'aliyun',
            'suggestion': overall_suggestion,
            'flagged_scenes': flagged_scenes
        }
    
    def _call_tencent_api(self, image_bytes: bytes, image_url: str = None) -> Tuple[bool, str, dict]:
        """
        调用腾讯云数据万象图片审核 API
        
        使用 COS 数据万象的图片单次审核接口
        文档: https://cloud.tencent.com/document/product/460/72995
        
        Args:
            image_bytes: 图片二进制数据（用于计算签名时的备用）
            image_url: 图片公网URL（推荐使用，避免上传图片到COS）
        """
        if not self.tencent_bucket or not self.tencent_region:
            logger.warning("Tencent COS bucket or region not configured")
            return True, "skip", {"status": "tencent_config_missing"}
        
        # 使用 detect-url 参数审核公网图片
        # 这样不需要先上传到 COS
        if not image_url:
            logger.warning("Tencent audit requires image_url for detect-url mode")
            return True, "skip", {"status": "no_image_url"}
        
        try:
            # 构建请求
            host = f"{self.tencent_bucket}.cos.{self.tencent_region}.myqcloud.com"
            
            # 使用 detect-url 审核任意公网图片
            # 请求路径使用一个虚拟的 ObjectKey
            path = "/"
            query_params = {
                "ci-process": "sensitive-content-recognition",
                "detect-url": image_url,
            }
            
            # 生成签名
            authorization = self._generate_tencent_signature(
                method="GET",
                host=host,
                path=path,
                query_params=query_params
            )
            
            # 构建完整URL
            query_string = urllib.parse.urlencode(query_params)
            url = f"https://{host}{path}?{query_string}"
            
            headers = {
                "Host": host,
                "Authorization": authorization,
            }
            
            # 发送请求
            with httpx.Client(timeout=20.0) as client:
                response = client.get(url, headers=headers)
            
            if response.status_code != 200:
                error_text = response.text[:500]
                logger.error(f"Tencent audit API error: {response.status_code} - {error_text}")
                
                # 检查是否是 NoSuchKey 错误（可重试）
                is_retryable = "NoSuchKey" in error_text or "AccessDenied" in error_text
                
                return True, "error", {
                    "status": "api_error",
                    "http_code": response.status_code,
                    "message": error_text,
                    "retryable": is_retryable  # 标记是否可重试
                }
            
            # 解析 XML 响应
            return self._parse_tencent_response(response.text)
            
        except httpx.TimeoutException as e:
            logger.error(f"Tencent audit timeout: {e}")
            return True, "error", {"status": "timeout", "message": str(e), "retryable": True}
        except httpx.ConnectError as e:
            logger.error(f"Tencent audit connection error: {e}")
            return True, "error", {"status": "connection_error", "message": str(e), "retryable": True}
        except Exception as e:
            logger.error(f"Tencent audit exception: {e}")
            return True, "error", {"status": "exception", "message": str(e)[:500], "retryable": False}
    
    def _generate_tencent_signature(
        self, 
        method: str, 
        host: str, 
        path: str, 
        query_params: dict
    ) -> str:
        """
        生成腾讯云 COS 请求签名
        文档: https://cloud.tencent.com/document/product/436/7778
        """
        # SecretId 和 SecretKey
        secret_id = self.api_key
        secret_key = self.api_secret
        
        # 时间戳
        current_time = int(time.time())
        expire_time = current_time + 600  # 10分钟有效期
        
        # 签名有效时间
        key_time = f"{current_time};{expire_time}"
        
        # 生成 SignKey
        sign_key = hmac.new(
            secret_key.encode('utf-8'),
            key_time.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        # 生成 HttpString
        http_method = method.lower()
        uri_pathname = path
        
        # 排序并编码查询参数
        sorted_params = sorted(query_params.items())
        http_parameters = "&".join([
            f"{urllib.parse.quote(k.lower(), safe='')}={urllib.parse.quote(str(v), safe='')}"
            for k, v in sorted_params
        ])
        
        # 请求头（这里只用 host）
        http_headers = f"host={urllib.parse.quote(host.lower(), safe='')}"
        
        http_string = f"{http_method}\n{uri_pathname}\n{http_parameters}\n{http_headers}\n"
        
        # 生成 StringToSign
        sha1_http_string = hashlib.sha1(http_string.encode('utf-8')).hexdigest()
        string_to_sign = f"sha1\n{key_time}\n{sha1_http_string}\n"
        
        # 生成 Signature
        signature = hmac.new(
            sign_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).hexdigest()
        
        # 组装 Authorization
        # 参数列表（小写）
        param_list = ";".join(sorted([k.lower() for k in query_params.keys()]))
        header_list = "host"
        
        authorization = (
            f"q-sign-algorithm=sha1"
            f"&q-ak={secret_id}"
            f"&q-sign-time={key_time}"
            f"&q-key-time={key_time}"
            f"&q-header-list={header_list}"
            f"&q-url-param-list={param_list}"
            f"&q-signature={signature}"
        )
        
        return authorization
    
    def _parse_tencent_response(self, xml_text: str) -> Tuple[bool, str, dict]:
        """
        解析腾讯云审核响应 XML
        
        响应示例:
        <RecognitionResult>
            <JobId>xxx</JobId>
            <Result>0</Result>  <!-- 0=正常, 1=违规, 2=疑似 -->
            <Label>Normal</Label>
            <Score>0</Score>
            <PornInfo>
                <HitFlag>0</HitFlag>
                <Score>0</Score>
            </PornInfo>
        </RecognitionResult>
        """
        import xml.etree.ElementTree as ET
        
        try:
            root = ET.fromstring(xml_text)
            
            # 获取整体结果
            result_code = int(root.findtext('Result', '0'))
            label = root.findtext('Label', 'Normal')
            score = int(root.findtext('Score', '0'))
            job_id = root.findtext('JobId', '')
            
            # 收集各场景详情
            flagged_scenes = []
            
            for info_name in ['PornInfo', 'AdsInfo', 'QualityInfo']:
                info_elem = root.find(info_name)
                if info_elem is not None:
                    hit_flag = int(info_elem.findtext('HitFlag', '0'))
                    info_score = int(info_elem.findtext('Score', '0'))
                    info_label = info_elem.findtext('Label', '')
                    sub_label = info_elem.findtext('SubLabel', '')
                    
                    if hit_flag > 0:
                        flagged_scenes.append({
                            'scene': info_name.replace('Info', ''),
                            'hit_flag': hit_flag,
                            'score': info_score,
                            'label': info_label,
                            'sub_label': sub_label
                        })
            
            # 判断结果
            # Result: 0=正常, 1=违规, 2=疑似
            if result_code == 0:
                suggestion = 'pass'
                is_safe = True
            elif result_code == 1:
                suggestion = 'block'
                is_safe = False
            else:  # result_code == 2
                suggestion = 'review'
                is_safe = not self.auto_reject
            
            return is_safe, suggestion, {
                'provider': 'tencent',
                'job_id': job_id,
                'result_code': result_code,
                'label': label,
                'score': score,
                'suggestion': suggestion,
                'flagged_scenes': flagged_scenes
            }
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse Tencent response XML: {e}")
            logger.debug(f"XML content: {xml_text[:1000]}")
            return True, "error", {"status": "xml_parse_error", "message": str(e)}


async def run_audit_in_background(
    image_id: int,
    image_bytes: bytes,
    audit_service: 'ImageAuditService',
    image_url: str = None
):
    """
    后台异步执行审核任务（带重试机制）
    
    关键设计：
    1. 所有异常都被捕获，不会影响主进程
    2. 使用超时控制，避免长时间阻塞
    3. API错误时保持pending状态，不误封
    4. 数据库操作独立，失败不影响其他
    5. 对于可重试的错误（如 NoSuchKey），自动重试最多 MAX_RETRY_ATTEMPTS 次
    
    Args:
        image_id: 图片ID
        image_bytes: 图片二进制数据
        audit_service: 审核服务实例
        image_url: 图片公网URL（腾讯云审核需要）
    """
    logger.info(f"[Audit] Starting for image {image_id}, url={image_url}")
    
    # 初始延迟：等待文件完全写入磁盘并可通过公网访问
    # 这对于本地存储+Nginx代理的场景尤为重要
    await asyncio.sleep(INITIAL_DELAY)
    
    is_safe = True
    suggestion = "error"
    details = {"status": "unknown_error"}
    
    # 重试循环
    for attempt in range(MAX_RETRY_ATTEMPTS):
        try:
            # 使用 asyncio.to_thread (Python 3.9+) 或 run_in_executor
            loop = asyncio.get_running_loop()
            
            # 带超时的线程池执行
            future = loop.run_in_executor(
                _executor,
                lambda: audit_service.audit_image_sync(image_bytes, image_url)
            )
            
            # 设置超时
            is_safe, suggestion, details = await asyncio.wait_for(
                future, 
                timeout=AUDIT_TIMEOUT
            )
            
            logger.info(f"[Audit] Image {image_id} attempt {attempt + 1}: safe={is_safe}, suggestion={suggestion}")
            
            # 检查是否需要重试
            if suggestion == "error" and details.get("retryable", False):
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                    logger.warning(f"[Audit] Image {image_id}: Retryable error, waiting {retry_delay}s before retry {attempt + 2}/{MAX_RETRY_ATTEMPTS}")
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    logger.error(f"[Audit] Image {image_id}: Max retries ({MAX_RETRY_ATTEMPTS}) reached, giving up")
            
            # 成功或不可重试的错误，跳出循环
            break
            
        except asyncio.TimeoutError:
            logger.error(f"[Audit] Image {image_id} attempt {attempt + 1}: TIMEOUT after {AUDIT_TIMEOUT}s")
            is_safe = True
            suggestion = "error"
            details = {"status": "timeout", "message": f"Audit timeout after {AUDIT_TIMEOUT}s", "retryable": True}
            
            # 超时也可以重试
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                retry_delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                logger.warning(f"[Audit] Image {image_id}: Timeout, waiting {retry_delay}s before retry {attempt + 2}/{MAX_RETRY_ATTEMPTS}")
                await asyncio.sleep(retry_delay)
                continue
            
        except Exception as e:
            logger.error(f"[Audit] Image {image_id} attempt {attempt + 1}: Exception - {e}")
            is_safe = True
            suggestion = "error"
            details = {"status": "exception", "message": str(e)[:500], "retryable": False}
            break  # 未知异常不重试
    
    # 记录最终重试次数
    details["attempts"] = attempt + 1
    
    # 更新数据库（独立try块）
    try:
        await _update_image_status(image_id, is_safe, suggestion, details)
    except Exception as e:
        logger.error(f"[Audit] Image {image_id}: DB update failed - {e}")
    
    logger.info(f"[Audit] Image {image_id}: Complete after {attempt + 1} attempt(s)")


async def _update_image_status(
    image_id: int, 
    is_safe: bool, 
    suggestion: str, 
    details: dict
):
    """
    更新图片状态（独立函数，便于错误隔离）
    
    重要策略：
    - 审核成功：根据结果设置 approved 或 rejected
    - 审核跳过（配置问题）：自动通过
    - 审核失败（API错误）：保持 pending，记录错误信息（用户仍可访问 pending 图片）
    - 审核不通过：设置 rejected 并删除文件
    """
    from app.database import AsyncSessionLocal
    from app.models.image import Image, ImageStatus
    
    async with AsyncSessionLocal() as db:
        try:
            from sqlalchemy import select
            result = await db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()
            
            if not image:
                logger.error(f"[Audit] Image {image_id} not found in DB")
                return
            
            # 情况1：审核被跳过（未配置/未启用）- 直接通过
            skip_reasons = ("audit_disabled", "no_provider", "no_credentials", "sdk_not_installed", "tencent_config_missing", "no_image_url")
            if suggestion == "skip" and details.get("status") in skip_reasons:
                image.status = ImageStatus.APPROVED
                image.audit_result = json.dumps(details, ensure_ascii=False)
                await db.commit()
                logger.info(f"[Audit] Image {image_id}: AUTO-APPROVED (reason: {details.get('status')})")
                return
            
            # 情况2：API错误/超时 - 保持 pending，记录错误信息
            # 用户仍可访问 pending 状态的图片，不影响使用
            if suggestion in ("error", "skip"):
                attempts = details.get("attempts", 1)
                logger.warning(f"[Audit] Image {image_id}: Keeping PENDING after {attempts} attempts (reason: {details.get('status')})")
                image.audit_result = json.dumps(details, ensure_ascii=False)
                await db.commit()
                return
            
            # 情况3：审核通过
            if is_safe:
                image.status = ImageStatus.APPROVED
                image.audit_result = json.dumps(details, ensure_ascii=False)
                await db.commit()
                logger.info(f"[Audit] Image {image_id}: APPROVED")
                return
            
            # 情况4：审核不通过 - 拒绝并删除文件
            await _reject_image(db, image, details)
            
        except Exception as e:
            logger.error(f"[Audit] DB error for image {image_id}: {e}")
            await db.rollback()
            raise


async def _reject_image(db, image, details: dict):
    """
    拒绝图片：更新状态、记录违规、删除文件
    
    支持本地存储和云存储的文件删除
    """
    from app.models.image import ImageStatus
    from app.services import security as security_service
    from app.services.storage import get_storage_backend_async
    import os
    from app.config import get_settings
    
    image_id = image.id
    config = get_settings()
    
    # 获取文件路径（支持日期文件夹结构和旧的扁平结构）
    storage_path = image.file_path if image.file_path else image.full_filename
    
    # 更新状态
    image.status = ImageStatus.REJECTED
    image.audit_result = json.dumps(details, ensure_ascii=False)
    
    logger.warning(f"[Audit] Image {image_id} REJECTED: {details}")
    
    # 记录违规（独立try，失败不影响主流程）
    try:
        await security_service.log_violation(
            ip=image.upload_ip or image.guest_ip or "unknown",
            violation_type="audit_failed",
            user_id=image.user_id,
            image_id=image.id,
            details=details,
            db=db
        )
    except Exception as e:
        logger.error(f"[Audit] Failed to log violation for image {image_id}: {e}")
    
    # 提交数据库更改
    await db.commit()
    logger.info(f"[Audit] Image {image_id} status committed as REJECTED")
    
    # 删除文件（独立try，失败不影响主流程）
    # 支持本地存储和云存储
    try:
        storage = await get_storage_backend_async()
        deleted = await storage.delete(storage_path)
        if deleted:
            logger.info(f"[Audit] Deleted file via storage backend: {storage_path}")
        else:
            logger.warning(f"[Audit] File deletion returned False: {storage_path}")
    except Exception as e:
        logger.error(f"[Audit] Failed to delete file {storage_path}: {e}")
        # 如果通过存储后端删除失败，尝试直接删除本地文件（兜底）
        if image.storage_type == "local":
            try:
                local_path = os.path.join(config.upload_path, storage_path)
                if os.path.exists(local_path):
                    os.remove(local_path)
                    logger.info(f"[Audit] Deleted local file (fallback): {local_path}")
            except Exception as e2:
                logger.error(f"[Audit] Fallback local delete also failed: {e2}")


async def get_audit_service() -> ImageAuditService:
    """获取审核服务实例"""
    from app.services import settings as settings_service
    
    try:
        enabled = await settings_service.is_audit_enabled()
        provider = await settings_service.get_audit_provider()
        api_key = await settings_service.get_audit_api_key()
        api_secret = await settings_service.get_audit_api_secret()
        auto_reject = await settings_service.is_audit_auto_reject()
        
        # 腾讯云特有配置 - 使用审核专用的 Bucket 和 Region 配置
        tencent_bucket = ""
        tencent_region = ""
        if provider == "tencent":
            tencent_bucket = await settings_service.get_setting("audit_tencent_bucket", "")
            tencent_region = await settings_service.get_setting("audit_tencent_region", "")
        
        return ImageAuditService(
            enabled=enabled,
            provider=provider,
            api_key=api_key,
            api_secret=api_secret,
            auto_reject=auto_reject,
            tencent_bucket=tencent_bucket,
            tencent_region=tencent_region
        )
    except Exception as e:
        logger.error(f"[Audit] Failed to load settings: {e}")
        return ImageAuditService(False, "", "", "", False, "", "")
