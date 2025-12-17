/**
 * Timezone utility for converting UTC times to system timezone
 * 
 * IMPORTANT: Backend returns times in UTC without timezone suffix.
 * We need to treat all incoming times as UTC and convert to display timezone.
 */

/**
 * Parse a date string as UTC
 * Backend returns dates like "2024-12-14T10:30:00" without Z suffix
 * JavaScript would parse this as local time, so we need to force UTC interpretation
 * 
 * @param {string|Date} dateInput - Date string or Date object
 * @returns {Date|null} - Date object interpreted as UTC
 */
function parseAsUTC(dateInput) {
  if (!dateInput) return null
  
  if (dateInput instanceof Date) {
    return dateInput
  }
  
  let dateStr = String(dateInput)
  
  // If the string doesn't have timezone info, append Z to treat as UTC
  // This handles formats like "2024-12-14T10:30:00" or "2024-12-14 10:30:00"
  if (!dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
    // Replace space with T for ISO format compatibility
    dateStr = dateStr.replace(' ', 'T')
    // Append Z to indicate UTC
    dateStr = dateStr + 'Z'
  }
  
  const date = new Date(dateStr)
  return isNaN(date.getTime()) ? null : date
}

/**
 * Format date to localized string in specified timezone
 * 
 * @param {string|Date} dateInput - UTC date string or Date object
 * @param {string} timezone - Target timezone (e.g., 'Asia/Shanghai')
 * @param {object} options - Additional Intl.DateTimeFormat options
 * @returns {string} - Formatted date string in target timezone
 */
export function formatDateTime(dateInput, timezone = 'Asia/Shanghai', options = {}) {
  if (!dateInput) return '-'
  
  const date = parseAsUTC(dateInput)
  if (!date) return '-'
  
  const defaultOptions = {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
    timeZone: timezone,
  }
  
  try {
    // Use Intl.DateTimeFormat for proper timezone conversion
    const formatter = new Intl.DateTimeFormat('zh-CN', { ...defaultOptions, ...options })
    return formatter.format(date)
  } catch (e) {
    // Fallback for unsupported timezones - use manual offset calculation
    console.warn(`Timezone ${timezone} not supported, using fallback`, e)
    return fallbackFormat(date, timezone)
  }
}

/**
 * Fallback format function for browsers that don't support the timezone
 */
function fallbackFormat(date, timezone) {
  // Timezone offset map (in minutes from UTC)
  const TIMEZONE_OFFSETS = {
    'Asia/Shanghai': 480,      // UTC+8
    'Asia/Tokyo': 540,         // UTC+9
    'Asia/Singapore': 480,     // UTC+8
    'Asia/Hong_Kong': 480,     // UTC+8
    'UTC': 0,                  // UTC
    'America/New_York': -300,  // UTC-5 (EST)
    'America/Los_Angeles': -480, // UTC-8 (PST)
    'Europe/London': 0,        // UTC+0 (GMT)
    'Europe/Paris': 60,        // UTC+1 (CET)
  }
  
  const offset = TIMEZONE_OFFSETS[timezone] ?? 480 // Default to UTC+8
  const adjustedTime = new Date(date.getTime() + offset * 60 * 1000)
  
  const year = adjustedTime.getUTCFullYear()
  const month = String(adjustedTime.getUTCMonth() + 1).padStart(2, '0')
  const day = String(adjustedTime.getUTCDate()).padStart(2, '0')
  const hours = String(adjustedTime.getUTCHours()).padStart(2, '0')
  const minutes = String(adjustedTime.getUTCMinutes()).padStart(2, '0')
  const seconds = String(adjustedTime.getUTCSeconds()).padStart(2, '0')
  
  return `${year}/${month}/${day} ${hours}:${minutes}:${seconds}`
}

/**
 * Format date only (no time)
 * 
 * @param {string|Date} dateInput - UTC date string or Date object
 * @param {string} timezone - Target timezone
 * @returns {string} - Formatted date string (YYYY/MM/DD)
 */
export function formatDate(dateInput, timezone = 'Asia/Shanghai') {
  return formatDateTime(dateInput, timezone, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: undefined,
    minute: undefined,
    second: undefined,
  })
}

/**
 * Format time only (no date)
 * 
 * @param {string|Date} dateInput - UTC date string or Date object
 * @param {string} timezone - Target timezone
 * @returns {string} - Formatted time string (HH:MM:SS)
 */
export function formatTime(dateInput, timezone = 'Asia/Shanghai') {
  return formatDateTime(dateInput, timezone, {
    year: undefined,
    month: undefined,
    day: undefined,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

/**
 * Get relative time string (e.g., "5 minutes ago")
 * 
 * @param {string|Date} dateInput - UTC date string or Date object
 * @param {string} timezone - Target timezone (used for fallback to absolute time)
 * @returns {string} - Relative time string or formatted date
 */
export function formatRelativeTime(dateInput, timezone = 'Asia/Shanghai') {
  if (!dateInput) return '-'
  
  const date = parseAsUTC(dateInput)
  if (!date) return '-'
  
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (seconds < 0) return formatDateTime(dateInput, timezone) // Future time
  if (seconds < 60) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return formatDateTime(dateInput, timezone)
}

/**
 * Convert a UTC date to the specified timezone and return as Date object
 * 
 * @param {string|Date} dateInput - UTC date string or Date object
 * @param {string} timezone - Target timezone
 * @returns {Date|null} - Date object in target timezone (for display purposes)
 */
export function convertToTimezone(dateInput, timezone = 'Asia/Shanghai') {
  if (!dateInput) return null
  
  const date = parseAsUTC(dateInput)
  if (!date) return null
  
  // Note: This returns a Date object that, when displayed using UTC methods,
  // will show the time in the target timezone
  const TIMEZONE_OFFSETS = {
    'Asia/Shanghai': 480,
    'Asia/Tokyo': 540,
    'Asia/Singapore': 480,
    'Asia/Hong_Kong': 480,
    'UTC': 0,
    'America/New_York': -300,
    'America/Los_Angeles': -480,
    'Europe/London': 0,
    'Europe/Paris': 60,
  }
  
  const offset = TIMEZONE_OFFSETS[timezone] ?? 480
  return new Date(date.getTime() + offset * 60 * 1000)
}
