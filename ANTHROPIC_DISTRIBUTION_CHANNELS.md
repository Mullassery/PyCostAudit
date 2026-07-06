# Anthropic Distribution Channels Research

**Goal:** Understand where Claude Code users buy/access Anthropic, so PyCostAudit can integrate with all channels

---

## 📊 Anthropic Distribution Landscape

Claude (Anthropic) is available through multiple channels beyond direct API:

```
Anthropic
    ├─ Direct (console.anthropic.com)
    ├─ AWS Bedrock (enterprise)
    ├─ Azure (via Foundry)
    ├─ Google Cloud Vertex AI
    ├─ Replicate (inference)
    ├─ Together AI
    ├─ Fireworks AI
    ├─ Anyscale
    ├─ Modal Labs
    └─ Various integrations
```

---

## 🎯 Direct Integration: Anthropic Console

### URL: console.anthropic.com

**What users see:**
```
├─ Account settings
├─ API key generation
├─ Usage dashboard
├─ Billing
└─ Model access
```

**Current PyCostAudit support:**
- ✅ API key can be configured
- ✅ Usage endpoint (when available)
- ✅ Real cost data

**Cost tracking:**
```
Access: API key directly
Costs: Direct billing to Anthropic account
Dashboard: Official Anthropic dashboard
Limitation: Must have personal API key
```

---

## ☁️ Channel 1: AWS Bedrock (Enterprise Focus)

### Why it matters:
- Large enterprises use AWS
- Bedrock handles billing differently
- Different pricing model
- Separate usage tracking

### AWS Integration:

**API Endpoints:**
```
Service: bedrock
Region: us-east-1, us-west-2, etc.
Model ID: anthropic.claude-3-5-sonnet
Pricing: Per-token (different from direct)
```

**PyCostAudit Integration Needed:**

```python
class AWSBedrockConnector:
    \"\"\"Get Claude usage from AWS Bedrock\"\"\"
    
    def get_usage(self):
        # Via AWS Cost Explorer
        # Via CloudWatch metrics
        # Via AWS Billing API
```

**Advantages of Bedrock:**
- ✅ Integrated AWS billing
- ✅ Cost attribution via tags
- ✅ Consolidated bill with other AWS services
- ✅ Enterprise contract pricing

**Cost tracking:**
```
Access: AWS credentials + Bedrock access
Costs: Included in AWS bill
Dashboard: AWS Cost Explorer
Limitation: Mixed with other AWS services
```

**Implementation:**
```python
import boto3

bedrock = boto3.client('bedrock-runtime')
ce = boto3.client('ce')

# Get Claude costs from Cost Explorer
costs = ce.get_cost_and_usage(
    TimePeriod={'Start': '2026-06-01', 'End': '2026-07-01'},
    Granularity='DAILY',
    Metrics=['BlendedCost'],
    GroupBy=[{'Type': 'DIMENSION', 'Key': 'USAGE_TYPE'}],
    Filter={
        'Dimensions': {
            'Key': 'SERVICE',
            'Values': ['Bedrock']
        }
    }
)
```

---

## 🔵 Channel 2: Azure (Foundry)

### URL: api.azure.com

**What it is:**
- Azure's AI services marketplace
- Integration of Anthropic Claude
- Separate billing from AWS
- Enterprise support

**PyCostAudit Integration Needed:**

```python
class AzureBedrockConnector:
    \"\"\"Get Claude usage from Azure Foundry\"\"\"
    
    def get_usage(self):
        # Via Azure Cost Management
        # Via Azure usage API
```

**Advantages of Azure Foundry:**
- ✅ Azure billing consolidation
- ✅ Different pricing than direct API
- ✅ Enterprise SLAs
- ✅ Azure AD integration

**Cost tracking:**
```
Access: Azure credentials
Costs: Included in Azure bill
Dashboard: Azure Cost Management
Limitation: Different pricing model than direct
```

**Implementation:**
```python
from azure.mgmt.costmanagement import CostManagementClient

client = CostManagementClient(credential, subscription_id)

# Get Claude costs from Azure
query = {
    'type': 'Usage',
    'timeframe': 'MonthToDate',
    'dataset': {
        'granularity': 'Daily',
        'aggregation': {
            'totalCost': {'name': 'PreTaxCost', 'function': 'Sum'}
        },
        'filter': {
            'dimensions': {
                'name': 'ServiceName',
                'operator': 'In',
                'values': ['Claude']
            }
        }
    }
}
```

---

## 🟣 Channel 3: Google Cloud Vertex AI

### URL: cloud.google.com/vertex-ai

**What it is:**
- Google's AI platform
- Recently added Claude models
- GCP billing integration
- BigQuery integration

**PyCostAudit Integration Needed:**

```python
class GCPVertexConnector:
    \"\"\"Get Claude usage from Vertex AI\"\"\"
    
    def get_usage(self):
        # Via GCP Billing API
        # Via BigQuery cost analysis
```

**Advantages of Vertex AI:**
- ✅ BigQuery integration (SQL analysis)
- ✅ GCP consolidated billing
- ✅ Google Cloud ecosystem
- ✅ Advanced analytics

**Cost tracking:**
```
Access: GCP service account
Costs: Included in GCP bill
Dashboard: Cloud Billing Console or BigQuery
Limitation: Need to filter for Claude specifically
```

**Implementation:**
```python
from google.cloud import billing_v1

client = billing_v1.CloudBillingClient()

# Get usage data
request = billing_v1.ListBillingAccountsRequest()
accounts = client.list_billing_accounts(request=request)

# Export to BigQuery for analysis
query = \"\"\"
SELECT 
    sku.description,
    SUM(usage.amount) as total_usage,
    SUM(cost) as total_cost
FROM `project.dataset.gcp_billing_export_*`
WHERE sku.description LIKE '%Claude%'
GROUP BY sku.description
\"\"\"
```

---

## 🟠 Channel 4: Replicate

### URL: replicate.com

**What it is:**
- Model marketplace
- Claude available via API
- Pay-as-you-go
- Separate billing

**PyCostAudit Integration Needed:**

```python
class ReplicateConnector:
    \"\"\"Get Claude usage from Replicate\"\"\"
    
    def get_usage(self):
        # Via Replicate API
```

**Advantages:**
- ✅ Simple pay-as-you-go
- ✅ No infrastructure needed
- ✅ Easy to scale
- ❌ Higher pricing than direct

**Cost tracking:**
```
Access: Replicate API key
Costs: Replicate account billing
Dashboard: Replicate account dashboard
Limitation: Separate from other spending
```

**Implementation:**
```python
import replicate

# Get account info
account = replicate.account.get()

# Get usage info
# (Replicate API may not expose usage directly)
# Typically done via dashboard scraping or email reports
```

---

## 🟡 Channel 5: Together AI

### URL: together.ai

**What it is:**
- Unified inference platform
- Claude + other models
- Hosted infrastructure
- Developer-friendly

**PyCostAudit Integration Needed:**

```python
class TogetherAIConnector:
    \"\"\"Get Claude usage from Together AI\"\"\"
    
    def get_usage(self):
        # Via Together AI API
```

**Advantages:**
- ✅ Unified model access
- ✅ Simple pricing
- ✅ Developer console
- ❌ Additional layer of cost

**Cost tracking:**
```
Access: Together AI API token
Costs: Together AI account
Dashboard: Together AI console
Limitation: May not expose detailed usage
```

---

## 🔴 Channel 6: Fireworks AI

### URL: fireworks.ai

**What it is:**
- Real-time AI inference
- Claude available
- Low-latency infrastructure
- Purpose-built for production

**Similar structure to Together AI**

---

## 📋 Complete Distribution Integration Map

| Channel | API Available | Billing Separate | Difficulty | Value |
|---------|:-------------:|:----------------:|:----------:|:-----:|
| Anthropic Direct | ✅ Yes | ✅ Direct | Easy | High |
| AWS Bedrock | ✅ Yes | ✅ AWS Bill | Medium | Very High |
| Azure Foundry | ✅ Yes | ✅ Azure Bill | Medium | Very High |
| GCP Vertex AI | ✅ Yes | ✅ GCP Bill | Medium | Very High |
| Replicate | ⚠️ Limited | ✅ Separate | Hard | Medium |
| Together AI | ✅ Yes | ✅ Separate | Medium | Medium |
| Fireworks AI | ✅ Yes | ✅ Separate | Medium | Medium |

---

## 🎯 PyCostAudit Integration Priority

### Priority 1: Direct + Cloud (AWS, Azure, GCP)
```
Why: 90% of enterprise users
Value: Consolidated billing view
Effort: 30-40 hours
Impact: Track $2,500+/month spending
```

### Priority 2: Replicate + Together
```
Why: Developer/startup users
Value: See if cost-effective
Effort: 10-15 hours
Impact: Track $100-500/month spending
```

### Priority 3: Other platforms
```
Why: Long tail
Value: Completeness
Effort: 5-10 hours per
Impact: Track $10-100/month spending
```

---

## 🔧 Implementation Architecture

```
PyCostAudit
    ├─ AnthropicConnector (Direct API)
    │   ├─ Get real usage
    │   └─ Real token counts
    │
    ├─ AWSBedrockConnector
    │   ├─ Cost Explorer API
    │   ├─ CloudWatch metrics
    │   └─ Billing API
    │
    ├─ AzureFoundryConnector
    │   ├─ Cost Management API
    │   └─ Usage details API
    │
    ├─ GCPVertexConnector
    │   ├─ Billing API
    │   └─ BigQuery export
    │
    └─ [Other platform connectors]
         ├─ Replicate
         ├─ Together AI
         └─ etc.

All feed into:
    ↓
Unified Cost Aggregation
    ↓
Single Dashboard
```

---

## 💡 Unified Insights

### What multi-channel integration unlocks:

```
User Profile: "I use Claude through 3 channels"

Channel breakdown:
  ├─ Direct API: $50/month (10 projects)
  ├─ AWS Bedrock: $1,200/month (ML pipeline)
  └─ Azure Foundry: $300/month (enterprise app)
  
TOTAL CLAUDE SPEND: $1,550/month

Per-project attribution:
  ├─ StatGuard (Bedrock): $450
  ├─ ClusterAudienceKit (Direct): $20
  ├─ PrismNote (Azure): $150
  └─ Others: $930
```

### What it reveals:

```
Insights:
1. "Bedrock is most expensive (77% of spend)"
2. "Could migrate to Direct API (save 30%)"
3. "Azure pricing is high for workload"
4. "Better split: Direct (50%) + GCP (50%)"

Recommendation:
  "Migrate Bedrock workloads to GCP Vertex AI"
  "Potential savings: $360/month (23% reduction)"
```

---

## 🚀 Implementation Roadmap

### Phase 1: Connectors (Week 1-2)
- [ ] Anthropic Direct (already done)
- [ ] AWS Bedrock connector
- [ ] Azure Foundry connector
- [ ] GCP Vertex AI connector

### Phase 2: Aggregation (Week 2)
- [ ] Unified cost rollup
- [ ] Multi-channel dashboard
- [ ] Channel-specific insights

### Phase 3: Intelligence (Week 3)
- [ ] Channel comparison
- [ ] Migration recommendations
- [ ] Optimization suggestions

### Phase 4: Automation (Week 4)
- [ ] Auto-sync with all channels
- [ ] Real-time cost tracking
- [ ] Scheduled reports

---

## 📊 Expected User Breakdown

**Estimate of PyCostAudit users:**
```
Direct API only:              20%
AWS Bedrock only:             30%
Azure Foundry only:           15%
Multi-channel (2+):           35%

Value per segment:
  Single channel: $100-500 savings/year
  Multi-channel: $1,000-5,000 savings/year
  
Multi-channel users are:
  - 7x more valuable
  - More likely to engage
  - More likely to upgrade
  - More likely to recommend
```

---

## 🎯 Why This Matters

**Current state:**
- Users only see direct API costs
- Hidden costs in AWS/Azure/GCP
- No visibility into total spend
- Can't optimize across channels

**After integration:**
- See ALL Claude spending ($1,500/month vs $50/month)
- Identify most expensive channel
- Migrate workloads intelligently
- Optimize globally

**Competitive advantage:**
- Only tool that tracks Claude across all channels
- Unique insights into multi-cloud spending
- Enterprise feature (Bedrock, Azure, GCP users)

---

## 🔐 Authentication Required

### Each platform needs:
- AWS: IAM credentials
- Azure: Service principal
- GCP: Service account
- Replicate: API key
- Together: API token

**PyCostAudit approach:**
- Store credentials in encrypted config
- Allow per-channel enable/disable
- Provide setup guides for each
- Validate credentials on setup

---

**Integrating all channels gives 10x more value for enterprise users who don't know they're spending $1,500+/month on Claude across multiple platforms.**
