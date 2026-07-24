# outputs.tf
# Prints useful values after apply completes, instead of hunting through
# the AWS Console every time. Also used later by Ansible to know where to connect.

output "jenkins_public_ip" {
  description = "Public IP of the Jenkins server"
  value       = aws_instance.jenkins.public_ip
}

output "sonarqube_public_ip" {
  description = "Public IP of the SonarQube server"
  value       = aws_instance.sonarqube.public_ip
}

output "k3s_public_ip" {
  description = "Public IP of the k3s server"
  value       = aws_instance.k3s.public_ip
}

output "jenkins_private_ip" {
  description = "Private IP of Jenkins (used for internal communication)"
  value       = aws_instance.jenkins.private_ip
}

output "sonarqube_private_ip" {
  description = "Private IP of SonarQube (used for internal communication)"
  value       = aws_instance.sonarqube.private_ip
}

output "k3s_private_ip" {
  description = "Private IP of k3s (used for internal communication)"
  value       = aws_instance.k3s.private_ip
}