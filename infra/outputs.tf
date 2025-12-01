output "project_name" {
  value       = var.project_name
  description = "Project name prefix used for resources."
}

output "region" {
  value       = var.region
  description = "AWS region."
}

output "vpc_id" {
  value       = aws_vpc.eks_vpc.id
  description = "VPC ID."
}

output "public_subnet_id" {
  value       = aws_subnet.eks_pub_sub.id
  description = "Public subnet ID."
}

output "private_subnet_id" {
  value       = aws_subnet.eks_priv_sub.id
  description = "Private subnet ID."
}

output "eks_cluster_name" {
  value       = aws_eks_cluster.lili_cluster.name
  description = "EKS cluster name."
}

output "eks_cluster_endpoint" {
  value       = aws_eks_cluster.lili_cluster.endpoint
  description = "EKS API server endpoint."
}

output "eks_cluster_ca_certificate" {
  value       = aws_eks_cluster.lili_cluster.certificate_authority[0].data
  description = "Base64 encoded cluster CA certificate."
}
