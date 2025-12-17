<template>
  <div class="not-found">
    <div class="not-found__content">
      <div class="not-found__icon">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="12" r="10"/>
          <path d="M16 16s-1.5-2-4-2-4 2-4 2"/>
          <line x1="9" y1="9" x2="9.01" y2="9"/>
          <line x1="15" y1="9" x2="15.01" y2="9"/>
        </svg>
      </div>
      <h1 class="not-found__code">404</h1>
      <p class="not-found__text">{{ $t('notFound.description') }}</p>
      <router-link to="/" class="btn btn--primary btn--lg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9,22 9,12 15,12 15,22"/>
        </svg>
        {{ $t('notFound.backHome') }}
      </router-link>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.not-found {
  min-height: calc(100vh - 280px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  
  &__content {
    text-align: center;
  }
  
  &__icon {
    width: 120px;
    height: 120px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 24px;
    background: var(--bg-secondary);
    border-radius: 50%;
    color: var(--text-tertiary);
  }
  
  &__code {
    font-size: 72px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 8px;
    line-height: 1;
  }
  
  &__text {
    font-size: 16px;
    color: var(--text-tertiary);
    margin: 0 0 32px;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 28px;
  font-size: 15px;
  font-weight: 500;
  text-decoration: none;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.15s;
  
  &--primary {
    background: var(--accent-primary);
    color: var(--text-inverse);
    
    &:hover { opacity: 0.9; }
  }
  
  &--lg {
    padding: 16px 32px;
  }
}
</style>
