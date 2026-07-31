# security_groups.tf
# One security group per server, matching our architecture diagram.
# Principle: SSH and dashboard UIs -> only your IP.
# Inter-server traffic (Jenkins -> SonarQube, Jenkins -> k3s) -> only from each other's SG.

# ---------- Jenkins Security Group (EC2-1) ----------

resource "aws_security_group" "jenkins_sg" {
  name        = "jenkins-sg"
  description = "Security group for Jenkins server"
  vpc_id      = aws_vpc.devsecops_vpc.id

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Jenkins UI from my IP only"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "Allow all outbound (needed for apt, Docker Hub, GitHub, etc.)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "jenkins-sg"
  }
}
# ---------- SonarQube Security Group (EC2-2) ----------
resource "aws_security_group" "sonarqube_sg" {
  name        = "sonarqube-sg"
  description = "Security group for SonarQube server"
  vpc_id      = aws_vpc.devsecops_vpc.id

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "SonarQube UI from my IP only"
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description     = "Allow Jenkins to reach SonarQube API on port 9000 internally"
    from_port       = 9000
    to_port         = 9000
    protocol        = "tcp"
    security_groups = [aws_security_group.jenkins_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "sonarqube-sg"
  }
}

# ---------- k3s Security Group (EC2-3) ----------
resource "aws_security_group" "k3s_sg" {
  name        = "k3s-sg"
  description = "Security group for k3s cluster (app, ArgoCD, Prometheus, Grafana)"
  vpc_id      = aws_vpc.devsecops_vpc.id

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description     = "k3s API server, reachable from Jenkins for kubectl/helm/ArgoCD sync"
    from_port       = 6443
    to_port         = 6443
    protocol        = "tcp"
    security_groups = [aws_security_group.jenkins_sg.id]
  }

  ingress {
    description = "NodePort range for accessing the deployed app from my browser"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Grafana UI from my IP"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Prometheus UI from my IP"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "ArgoCD UI from my IP"
    from_port   = 8081
    to_port     = 8081
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "k3s-sg"
  }
}

# ---------- Monitoring Security Group (EC2-4) ----------
resource "aws_security_group" "monitoring_sg" {
  name        = "monitoring-sg"
  description = "Security group for Prometheus and Grafana server"
  vpc_id      = aws_vpc.devsecops_vpc.id

  ingress {
    description = "SSH from my IP only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Grafana UI from my IP"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description = "Prometheus UI from my IP"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  ingress {
    description     = "Allow Prometheus to scrape k3s metrics"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.k3s_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "monitoring-sg"
  }
}