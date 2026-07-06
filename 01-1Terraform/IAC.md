# IaC with Terraform — GCP Setup

## What is IaC

Infrastructure as Code means defining cloud resources (buckets, datasets, VMs) in files instead of clicking through the GCP console. Terraform reads these files and creates/updates/destroys resources to match.

---

## GCP Auth

No JSON key file needed. Authenticate via CLI:

```bash
gcloud auth application-default login
```

Terraform picks up credentials automatically from `~/.config/gcloud/application_default_credentials.json`.

---

## File Structure

```
Terraform/
├── main.tf        # provider config + resources
└── variables.tf   # input variables with defaults
```

---

## Flow

```
variables.tf        main.tf
(defaults/inputs) ──► provider "google" (project, region, zone)
                  ──► resource: GCS Bucket
                  ──► resource: BigQuery Dataset
        │
        │  terraform init
        ▼
Download google provider plugin (hashicorp/google v6.8.0)
        │
        │  terraform plan
        ▼
Show what will be created/changed (dry run)
        │
        │  terraform apply
        ▼
GCS Bucket  →  terraform-demo-498018-demo-bucket
BQ Dataset  →  demo_dataset
        │
        │  terraform destroy
        ▼
Resources deleted
```

---

## Resources Created

### GCS Bucket (`main.tf:18`)
- `force_destroy = true` — allows deleting even if bucket has files
- `uniform_bucket_level_access = true` — IAM-only access, no ACLs
- Lifecycle rule: delete objects after **3 days**
- Lifecycle rule: abort incomplete multipart uploads after **1 day**

### BigQuery Dataset (`main.tf:44`)
- `dataset_id` from `var.bg_dataset_name` → `demo_dataset`
- `location` from `var.location` → `US`

---

## Commands

```bash
terraform init      # download provider plugins
terraform plan      # preview changes
terraform apply     # create resources
terraform destroy   # tear down all resources
```
