# Design: Web Dashboard (Phase 2C)

**Status**: Design (Ready for implementation)  
**Timeline**: Week 2-3  
**Owner**: Frontend + Backend Developer  

---

## Overview

Real-time web dashboard for monitoring LLM costs across providers (OpenAI, Bedrock, Gemini). Provides cost visibility, breakdowns, trend analysis, and budget tracking.

**Users**: Finance teams, engineering leads, anyone needing cost visibility

---

## Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Frontend** | Next.js 14 (React) | Modern, SSR, API routes, built-in auth |
| **Backend** | FastAPI (Python) | Same language as PyCostAudit core, fast, async |
| **Database** | PostgreSQL | Time-series queries, scalable |
| **Auth** | NextAuth.js + JWT | Simple, stateless, OAuth-ready |
| **Real-time** | WebSocket (Socket.io) | Cost updates as they happen |
| **Charting** | Recharts (React) | Simple, performant cost visualization |

---

## Architecture

```
┌─────────────────────────────────────────────┐
│         Browser (Next.js Frontend)          │
│  ┌─────────────────────────────────────┐    │
│  │  Overview Page                      │    │
│  │  • Total spend (24h, 7d, 30d)       │    │
│  │  • Cost trend chart                 │    │
│  │  • Provider breakdown (pie/bar)     │    │
│  │  • Budget status                    │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │  Breakdown Page                     │    │
│  │  • By provider (OpenAI/Bedrock/etc) │    │
│  │  • By model (GPT-4, Claude 3, etc)  │    │
│  │  • By operation type                │    │
│  │  • Detailed call logs               │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │  Budget Tracking Page               │    │
│  │  • Budget vs. actual spend          │    │
│  │  • Daily burndown                   │    │
│  │  • Forecast (projected spend)       │    │
│  │  • Alerts & anomalies               │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
         ↓ REST API + WebSocket ↓
┌─────────────────────────────────────────────┐
│       FastAPI Backend (Python)              │
│  ┌─────────────────────────────────────┐    │
│  │  API Endpoints                      │    │
│  │  • GET /api/costs                   │    │
│  │  • GET /api/breakdown               │    │
│  │  • GET /api/budget                  │    │
│  │  • WebSocket /ws/costs (real-time)  │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │  Data Aggregation                   │    │
│  │  • Time-series rollup               │    │
│  │  • Caching (Redis)                  │    │
│  │  • Cost calculations                │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
         ↓ SQL ↓
┌─────────────────────────────────────────────┐
│     PostgreSQL Database                     │
│  ┌─────────────────────────────────────┐    │
│  │  costs                              │    │
│  │  • id, timestamp, provider          │    │
│  │  • model, tokens, cost              │    │
│  │  • (indexed on timestamp, provider) │    │
│  └─────────────────────────────────────┘    │
│  ┌─────────────────────────────────────┐    │
│  │  budgets                            │    │
│  │  • id, amount, period               │    │
│  │  • alerts_enabled, thresholds       │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

---

## Frontend Pages

### 1. Overview Page (/)

```
┌──────────────────────────────────────────────┐
│  PyCostAudit Dashboard                       │
├──────────────────────────────────────────────┤
│  📊 Key Metrics                              │
│  ┌─────────────┬──────────┬─────────────┐    │
│  │ Today       │ This Week│ This Month  │    │
│  │ $12.34      │ $89.50   │ $234.67     │    │
│  └─────────────┴──────────┴─────────────┘    │
│                                              │
│  📈 Cost Trend (30 days)                    │
│  ┌──────────────────────────────────────┐    │
│  │                    ╱╲                │    │
│  │                  ╱    ╲              │    │
│  │  ────────────╱────────╲──────        │    │
│  │             Day      Day+30           │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  🏢 Provider Breakdown                       │
│  ┌────────────────────────────────────────┐  │
│  │ ● OpenAI:  $150 (63%)                 │  │
│  │ ● Bedrock: $70  (30%)                 │  │
│  │ ● Gemini:  $18  (7%)                  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  💰 Budget Status                            │
│  ┌────────────────────────────────────────┐  │
│  │ Budget: $500/month                     │  │
│  │ Spent:  $234.67 (47%)                  │  │
│  │ Remaining: $265.33                     │  │
│  │ Forecast: $445 (89% of budget)         │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  [Breakdown] [Budget] [Settings]             │
└──────────────────────────────────────────────┘
```

**Components**:
- MetricsCard (24h/7d/30d costs)
- CostTrendChart (line chart)
- ProviderBreakdownChart (pie chart)
- BudgetStatusCard
- Navigation tabs

**API Calls**:
```
GET /api/costs?period=24h,7d,30d
GET /api/breakdown?provider=*&period=30d
GET /api/budget/status
```

---

### 2. Breakdown Page (/breakdown)

```
┌──────────────────────────────────────────────┐
│  Cost Breakdown                              │
├──────────────────────────────────────────────┤
│  Group by: [Provider ▼] [Model] [Operation] │
│                                              │
│  Filters: [Date Range ▼] [Min Cost ▼]      │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │ Provider   │ Model      │ Count │ Cost │  │
│  ├────────────────────────────────────────┤  │
│  │ OpenAI     │ gpt-4      │ 1,234 │ $89  │  │
│  │ OpenAI     │ gpt-4-turbo│  567  │ $34  │  │
│  │ Bedrock    │ claude-3   │  890  │ $45  │  │
│  │ Gemini     │ gemini-pro │  123  │ $2   │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  [Export CSV] [Export JSON]                  │
└──────────────────────────────────────────────┘
```

**Components**:
- GroupBySelector (provider, model, operation)
- FilterPanel (date range, min cost)
- DataTable (sortable, paginated)
- ExportButtons

**API Calls**:
```
GET /api/breakdown?group_by=provider&period=30d
GET /api/breakdown?group_by=model&period=7d
GET /api/breakdown?group_by=operation&provider=openai
```

---

### 3. Budget Tracking Page (/budget)

```
┌──────────────────────────────────────────────┐
│  Budget Tracking                             │
├──────────────────────────────────────────────┤
│  Monthly Budget: $500                        │
│  [Edit Budget]                               │
│                                              │
│  📊 This Month Progress                      │
│  ┌────────────────────────────────────────┐  │
│  │████████░░░░░░░░░░░░░░░░░░░░░░░  47%   │  │
│  │ $234 spent of $500 available            │  │
│  │ $265 remaining (13 days left)           │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  📈 Daily Burndown                           │
│  ┌────────────────────────────────────────┐  │
│  │   Budget line ─────────────────        │  │
│  │        ╱╲    Actual spend              │  │
│  │      ╱    ╲  ╱╲                        │  │
│  │    ╱───────╲╱  ╲                       │  │
│  │ Day 1             Day 13                │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  🎯 Forecast                                 │
│  ┌────────────────────────────────────────┐  │
│  │ Current burn rate: $18/day             │  │
│  │ Projected end-of-month: $445           │  │
│  │ Status: ✓ Within budget                │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  🔔 Alert Settings                           │
│  ☑ Alert when 75% of budget spent           │
│  ☑ Daily digest emails                      │
│  ☑ Slack notifications                      │
│                                              │
│  [Save Settings]                             │
└──────────────────────────────────────────────┘
```

**Components**:
- BudgetProgressBar
- BudgetEditor (modal to change limit)
- DailyBurndownChart
- ForecastCard
- AlertSettingsPanel

**API Calls**:
```
GET /api/budget/status
POST /api/budget/update
GET /api/budget/forecast
POST /api/budget/alerts
```

---

## Backend API Endpoints

### Authentication
```
POST /api/auth/register
POST /api/auth/login
GET /api/auth/me (current user)
POST /api/auth/logout
```

### Costs
```
GET /api/costs
  Query params: period=24h|7d|30d, provider=*, model=*, start_date=, end_date=
  Response: [{timestamp, provider, model, input_tokens, output_tokens, cost}, ...]

GET /api/breakdown
  Query params: group_by=provider|model|operation, period=, filters={}
  Response: [{group, total_cost, count, details}, ...]

GET /api/cost-summary
  Response: {total_today, total_7d, total_30d, by_provider, by_model}
```

### Budget
```
GET /api/budget/status
  Response: {budget_amount, spent, remaining, percent_used, forecast}

POST /api/budget/update
  Body: {amount, period}
  Response: {success, new_budget}

GET /api/budget/forecast
  Response: {daily_rate, projected_eom, status}
```

### Real-time Updates
```
WebSocket /ws/costs
  Message: {timestamp, provider, model, cost, total_today}
  Subscribe to real-time cost updates as they come in
```

---

## Frontend Components

### Layout Structure
```
src/
├── components/
│   ├── Layout.tsx (header, nav, footer)
│   ├── MetricsCard.tsx
│   ├── CostTrendChart.tsx
│   ├── ProviderBreakdownChart.tsx
│   ├── BudgetProgressBar.tsx
│   ├── FilterPanel.tsx
│   ├── DataTable.tsx
│   └── ...
├── pages/
│   ├── _app.tsx (NextAuth setup)
│   ├── index.tsx (overview)
│   ├── breakdown.tsx
│   ├── budget.tsx
│   └── api/auth/[...nextauth].ts
├── lib/
│   ├── api.ts (fetch wrappers)
│   ├── auth.ts (auth helpers)
│   ├── format.ts (formatting helpers)
│   └── ...
└── public/
    ├── favicon.ico
    └── ...
```

### Key Components

**MetricsCard**:
```typescript
interface MetricsCardProps {
  period: '24h' | '7d' | '30d'
  total_today: number
  total_7d: number
  total_30d: number
}

// Displays three cards showing costs for different periods
```

**CostTrendChart**:
```typescript
interface CostTrendChartProps {
  data: Array<{timestamp: string, cost: number}>
  period: '7d' | '30d' | '90d'
}

// Line chart using Recharts
```

**ProviderBreakdownChart**:
```typescript
interface ProviderBreakdownChartProps {
  data: Array<{provider: string, cost: number}>
}

// Pie chart showing cost distribution
```

---

## Data Models

### Cost Record
```python
class Cost(BaseModel):
    id: str
    timestamp: datetime
    provider: str  # 'openai', 'bedrock', 'gemini'
    model: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    metadata: dict = {}
```

### Budget
```python
class Budget(BaseModel):
    id: str
    user_id: str
    amount: float
    period: str  # 'monthly', 'weekly'
    created_at: datetime
    updated_at: datetime
```

### User
```python
class User(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
```

---

## Implementation Plan

### Week 1: Backend Setup
- [ ] Set up FastAPI project structure
- [ ] Create PostgreSQL schema (costs, budgets, users)
- [ ] Implement auth (NextAuth + JWT)
- [ ] Build cost aggregation APIs
- [ ] Add WebSocket support

### Week 2: Frontend Setup
- [ ] Set up Next.js project
- [ ] Create layout and navigation
- [ ] Build Overview page components
- [ ] Integrate with backend APIs
- [ ] Set up real-time updates

### Week 3: Polish
- [ ] Build Breakdown page
- [ ] Build Budget page
- [ ] Add data export (CSV/JSON)
- [ ] Performance optimization
- [ ] Responsive design (mobile-friendly)

---

## Success Criteria

- ✓ Real-time cost display (updates within 5 seconds)
- ✓ Multi-provider breakdown (OpenAI, Bedrock, Gemini)
- ✓ Budget tracking with forecast
- ✓ Mobile-responsive design
- ✓ <2s page load time
- ✓ All tests passing

---

## Security Considerations

- [ ] Encrypt sensitive data (API keys, budget info)
- [ ] Rate limit API endpoints
- [ ] Validate all user inputs
- [ ] Use HTTPS only
- [ ] Implement CSRF protection
- [ ] Session timeout (30 min of inactivity)

---

## Deployment

**Options**:
1. **Vercel** (frontend) + **Railway/Heroku** (backend)
2. **Docker Compose** (local/self-hosted)
3. **AWS ECS** (scalable, enterprise)

**Recommended for MVP**: Vercel + Railway (low-ops, good free tier)
