variable "location" {
  default = "US"

}



variable "bg_dataset_name" {
  description = "My Big query Dataset Name"
  default     = "demo_dataset"

}

variable "gcp_storage_class" {
  description = "Google Storage Bucket"
  default     = "terraform-demo-498018-demo-bucket"

}