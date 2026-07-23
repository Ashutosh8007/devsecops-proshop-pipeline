variable "my_ip" {
  description = "Your current public IP (CIDR /32), used to restrict SSH and dashboard access to only you"
  type        = string
}