# network.tf
# Defines the private network our 3 EC2 instances will live in,
# plus firewall rules (Security Groups) controlling what traffic is allowed.

# ---------- VPC ----------

resource "aws_vpc" "devsecops_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "devsecops-vpc"
  }
}

# ---------- Public Subnet ----------
# All 3 instances sit in one public subnet for simplicity (learning project).
# They get private IPs for internal traffic, and optional public IPs for our access.

resource "aws_subnet" "devsecops_public_subnet" {
  vpc_id                  = aws_vpc.devsecops_vpc.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "ap-south-1a"

  tags = {
    Name = "devsecops-public-subnet"
  }
}

# ---------- Internet Gateway ----------
# Lets resources in the VPC reach the internet (needed to pull Docker images,
# apt packages, GitHub, Docker Hub, etc.) and lets us reach the instances' public IPs.

resource "aws_internet_gateway" "devsecops_igw" {
  vpc_id = aws_vpc.devsecops_vpc.id

  tags = {
    Name = "devsecops-igw"
  }
}

# ---------- Route Table ----------
# Tells the subnet: "any traffic not meant for the local network (0.0.0.0/0)
# goes out through the Internet Gateway."

resource "aws_route_table" "devsecops_public_rt" {
  vpc_id = aws_vpc.devsecops_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.devsecops_igw.id
  }

  tags = {
    Name = "devsecops-public-rt"
  }
}

resource "aws_route_table_association" "devsecops_rt_assoc" {
  subnet_id      = aws_subnet.devsecops_public_subnet.id
  route_table_id = aws_route_table.devsecops_public_rt.id
}