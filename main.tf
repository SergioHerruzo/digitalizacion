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

# Variables per a Amplify
variable "github_repository" {
  type        = string
  description = "URL del repositori de GitHub (ex: https://github.com/usuari/repo)"
  default     = "https://github.com/SergioHerruzo/digitalizacion"
}

variable "github_token" {
  type        = string
  description = "Token d'accés personal de GitHub"
  sensitive   = true
  # S'ha eliminat el default per evitar errors 401. L'usuari l'ha de passar via CLI o tfvars.
}

# Obtenció dinàmica de la darrera AMI d'Amazon Linux 2023
data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

# 1. Instància EC2 per al motor de Python (Chatbot)
resource "aws_instance" "chatbot_engine" {
  ami           = data.aws_ami.amazon_linux_2023.id
  instance_type = "t2.micro"
  
  # Ús obligatori del LabRole existent a AWS Academy
  iam_instance_profile = "LabInstanceProfile"

  # Assignació del grup de seguretat
  vpc_security_group_ids = [aws_security_group.chatbot_sg.id]

  # Script d'arrencada (User Data)
  user_data = <<-EOF
              #!/bin/bash
              # 1. Preparació del sistema
              yum update -y
              yum install -y python3-pip git

              # 2. Configuració de l'espai de treball
              mkdir -p /home/ec2-user/app
              cd /home/ec2-user/app

              # 3. Descàrrega del codi (neteja prèvia per seguretat)
              rm -rf ./*
              git clone https://${var.github_token}@${replace(var.github_repository, "https://", "")} .

              # 4. Gestió de l'entorn Python (venv)
              python3 -m venv venv
              source venv/bin/activate

              # 5. Instal·lació de dependències
              pip install --upgrade pip
              pip install -r requirements.txt
              python -m spacy download es_core_news_md

              # 6. Correcció de permisos per a l'usuari ec2-user
              chown -R ec2-user:ec2-user /home/ec2-user/app

              # 7. Execució del backend en segon pla (usant la variable de la taula)
              export DYNAMODB_TABLE="${aws_dynamodb_table.conversations.name}"
              nohup venv/bin/python chatbot.py > /home/ec2-user/app/chatbot.log 2>&1 &
              EOF

  tags = {
    Name        = "Glovo-Chatbot-Server"
    Project     = "Transformacio-Digital"
    Environment = "Acadèmic"
  }
}

# Grup de Seguretat per permetre trànsit al xatbot i SSH
resource "aws_security_group" "chatbot_sg" {
  name        = "glovo-chatbot-sg"
  description = "Permetre port 5000 per al backend i 22 per SSH"

  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Flask API"
  }

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "SSH Access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Glovo-Security-Group"
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
  name           = "GlovoChatHistory-${random_id.suffix.hex}"
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

# 4. AWS Amplify per al Frontend (SPA)
resource "aws_amplify_app" "glovo_frontend" {
  name       = "Glovo-Digital-Frontend"
  repository = var.github_repository
  
  # Token d'accés per connectar amb GitHub
  access_token = var.github_token

  # Configuració de build: Inyectamos la IP de la EC2 en el index.html
  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        build:
          commands:
            - sed -i "s|__BACKEND_URL__|${aws_instance.chatbot_engine.public_ip}:5000|g" index.html
      artifacts:
        baseDirectory: /
        files:
          - '**/*'
      cache:
        paths: []
  EOT

  environment_variables = {
    ENV = "production"
  }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.glovo_frontend.id
  branch_name = "main"

  framework = "Web"
  stage     = "PRODUCTION"
}

output "amplify_app_url" {
  value = aws_amplify_app.glovo_frontend.default_domain
}

output "chatbot_public_ip" {
  value = aws_instance.chatbot_engine.public_ip
}
