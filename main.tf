# Configuration de la infraestructura per a Glovo
# Entorn: AWS Academy Learner Lab

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# 1. Instància EC2 per al motor de Python (Chatbot)
resource "aws_instance" "chatbot_engine" {
  ami           = "ami-04403f33f0c055235" # Amazon Linux 2023 AMI a us-east-1
  instance_type = "t2.micro"
  
  # Ús obligatori del LabRole existent a AWS Academy
  iam_instance_profile = "LabInstanceProfile"

  tags = {
    Name        = "Glovo-Chatbot-Server"
    Project     = "Transformacio-Digital"
    Environment = "Acadèmic"
  }
}

# 2. Bucket S3 per a dades no estructurades
resource "aws_s3_bucket" "glovo_assets" {
  bucket = "glovo-digital-transformation-assets-${random_id.suffix.hex}"
  
  # Les Acadèmies sovint bloquegen la creació de buckets depenent de la política,
  # però aquest és un recurs estàndard segons la petició.
}

resource "random_id" "suffix" {
  byte_length = 4
}

# 3. Taula DynamoDB per a la persistència de converses
resource "aws_dynamodb_table" "conversations" {
  name           = "GlovoChatHistory"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "SessionID"
  range_key      = "Timestamp"

  attribute {
    name = "SessionID"
    type = "S"
  }

  attribute {
    name = "Timestamp"
    type = "N"
  }

  tags = {
    Name = "Glovo-Chat-Persistence"
  }
}

output "chatbot_public_ip" {
  value = aws_instance.chatbot_engine.public_ip
}
