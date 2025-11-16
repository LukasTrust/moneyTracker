-- Migration 008: Add Insights System
-- Personalized spending insights with month-over-month and year-over-year comparisons
-- Created: 2025-11-16

-- ============================================================================
-- Table: insights
-- Stores generated spending insights for accounts
-- ============================================================================

CREATE TABLE IF NOT EXISTS insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Account relationship (NULL = global insight across all accounts)
    account_id INTEGER NULL,
    
    -- Insight type classification
    insight_type VARCHAR(50) NOT NULL,
    -- Types: 'mom_increase', 'mom_decrease', 'yoy_increase', 'yoy_decrease', 
    --        'top_growth_category', 'savings_potential', 'unusual_expense'
    
    -- Severity level for UI styling
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    -- Values: 'info', 'warning', 'success', 'alert'
    
    -- Insight content
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    
    -- Related data (JSON for flexibility)
    -- Note: Using 'insight_data' instead of 'metadata' to avoid SQLAlchemy reserved word conflict
    insight_data JSON NULL,
    -- Example: {"category_id": 5, "amount": 150.50, "percentage": 30.5, "period": "2025-10"}
    
    -- Display priority (higher = more important)
    priority INTEGER NOT NULL DEFAULT 5,
    
    -- Visibility tracking
    is_dismissed BOOLEAN NOT NULL DEFAULT 0,
    dismissed_at DATETIME NULL,
    
    -- Cooldown tracking (for popup re-appearance)
    last_shown_at DATETIME NULL,
    -- When was this insight last displayed to user
    
    show_count INTEGER NOT NULL DEFAULT 0,
    -- How many times this insight has been shown
    
    cooldown_hours INTEGER NOT NULL DEFAULT 24,
    -- Hours to wait before showing again (24h default)
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    valid_until DATETIME NULL,
    -- Insights can expire (e.g., monthly insights expire after 30 days)
    
    -- Foreign Keys
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_insights_account_id ON insights(account_id);
CREATE INDEX IF NOT EXISTS idx_insights_insight_type ON insights(insight_type);
CREATE INDEX IF NOT EXISTS idx_insights_is_dismissed ON insights(is_dismissed);
CREATE INDEX IF NOT EXISTS idx_insights_created_at ON insights(created_at);
CREATE INDEX IF NOT EXISTS idx_insights_priority ON insights(priority);
CREATE INDEX IF NOT EXISTS idx_insights_last_shown_at ON insights(last_shown_at);

-- Composite index for common queries (active insights for account)
CREATE INDEX IF NOT EXISTS idx_insights_active ON insights(account_id, is_dismissed, created_at) 
WHERE is_dismissed = 0;

-- Composite index for cooldown queries (ready to show)
CREATE INDEX IF NOT EXISTS idx_insights_cooldown ON insights(last_shown_at, cooldown_hours, is_dismissed);

-- ============================================================================
-- Table: insight_generation_log
-- Tracks when insights were last generated (to avoid duplicate generation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS insight_generation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Account relationship (NULL = global generation)
    account_id INTEGER NULL,
    
    -- Generation metadata
    generation_type VARCHAR(50) NOT NULL,
    -- Types: 'mom', 'yoy', 'savings_potential', 'full_analysis'
    
    insights_generated INTEGER NOT NULL DEFAULT 0,
    
    -- Timestamps
    generated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Additional info (JSON)
    generation_params JSON NULL,
    -- Example: {"from_date": "2025-10-01", "to_date": "2025-10-31"}
    
    -- Foreign Keys
    FOREIGN KEY (account_id) REFERENCES accounts (id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_insight_gen_log_account_id ON insight_generation_log(account_id);
CREATE INDEX IF NOT EXISTS idx_insight_gen_log_generated_at ON insight_generation_log(generated_at);
CREATE INDEX IF NOT EXISTS idx_insight_gen_log_type ON insight_generation_log(generation_type);

-- ============================================================================
-- Comments for documentation
-- ============================================================================

-- Insight Types:
-- 'mom_increase': Month-over-Month spending increase (threshold: >20%)
-- 'mom_decrease': Month-over-Month spending decrease (savings, threshold: >20%)
-- 'yoy_increase': Year-over-Year spending increase (threshold: >25%)
-- 'yoy_decrease': Year-over-Year spending decrease (savings, threshold: >25%)
-- 'top_growth_category': Category with highest growth (threshold: >30% and >50 EUR)
-- 'savings_potential': Detected unused subscriptions or cancelable services
-- 'unusual_expense': Single transaction significantly higher than average (threshold: >3x avg)

-- Severity Levels:
-- 'info': Neutral information (e.g., spending is stable)
-- 'success': Positive insight (e.g., spending decreased, savings achieved)
-- 'warning': Attention needed (e.g., spending increased moderately)
-- 'alert': Urgent attention (e.g., significant overspending, budget exceeded)

-- Priority:
-- 1-3: Low priority (informational)
-- 4-6: Medium priority (noteworthy)
-- 7-10: High priority (requires attention)
