# instances.tf
# Defines the 3 EC2 servers, the key pair AWS uses for SSH,
# and a minimal bootstrap script that runs once on first boot.

# ---------- Key Pair ----------
# Registers our locally-generated public key with AWS so it can be
# injected into each instance's authorized_keys on launch.
resource "aws_key_pair" "devsecops_key" {
  key_name   = "devsecops_key"
  public_key = file("${path.module}/keys/devsecops-key.pub")
}

# ---------- Ubuntu 24.04 AMI lookup ----------
# Instead of hardcoding an AMI ID (which is region-specific and changes
# over time as Canonical releases updates), we look it up dynamically.

data "aws_ami" "ubuntu_2404" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account ID
  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ---------- EC2-1: Jenkins ----------
resource "aws_instance" "jenkins" {
  ami                    = data.aws_ami.ubuntu_2404.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.devsecops_public_subnet.id
  vpc_security_group_ids = [aws_security_group.jenkins_sg.id]
  key_name               = aws_key_pair.devsecops_key.key_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
        #!/bin/bash
        apt-get update -y
        apt-get upgradde -y
        EOF

  tags = {
    Name = "jenkins-server"
  }
}

# ---------- EC2-2: SonarQube ----------

resource "aws_instance" "sonarqube" {
  ami                    = data.aws_ami.ubuntu_2404.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.devsecops_public_subnet.id
  vpc_security_group_ids = [aws_security_group.sonarqube_sg.id]
  key_name               = aws_key_pair.devsecops_key.key_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
        #!/bin/bash
        apt-get update -y
        apt-get upgrade -y
        EOF

  tags = {
    Name = "sonarqube-server"
  }
}

# ---------- EC2-3: k3s cluster ----------

resource "aws_instance" "k3s" {
  ami                    = data.aws_ami.ubuntu_2404.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.devsecops_public_subnet.id
  vpc_security_group_ids = [aws_security_group.k3s_sg.id]
  key_name               = aws_key_pair.devsecops_key.key_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
        #!/bin/bash
        apt-get update -y
        apt-get upgrade -y
        EOF

  tags = {
    Name = "k3s-server"
  }
}

# ---------- EC2-4: Monitoring (Prometheus + Grafana) ----------
resource "aws_instance" "monitoring" {
  ami                    = data.aws_ami.ubuntu_2404.id
  instance_type          = "t3.small"
  subnet_id              = aws_subnet.devsecops_public_subnet.id
  vpc_security_group_ids = [aws_security_group.monitoring_sg.id]
  key_name               = aws_key_pair.devsecops_key.key_name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get upgrade -y
              EOF

  tags = {
    Name = "monitoring-server"
  }
}