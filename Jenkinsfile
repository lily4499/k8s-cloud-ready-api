pipeline {
  agent any

  environment {
    AWS_DEFAULT_REGION = 'us-east-1'
    ECR_REPO           = '637423529262.dkr.ecr.us-east-1.amazonaws.com/cloud-ready-api'
  }

  stages {
    stage('Checkout') {
      steps {
        git branch: 'main', url: 'https://github.com/lily4499/k8s-cloud-ready-api.git'
      }
    }

    stage('Build & Unit Test') {
      steps {
        dir('app') {
          sh '''
            python3 -m venv venv
            . venv/bin/activate
            #source venv/bin/activate
            pip install -r requirements.txt
          '''
        }
      }
    }

    stage('Docker Build') {
      steps {
        dir('app') {
          script {
            IMAGE_TAG = "${env.BUILD_NUMBER}"
            sh """
              docker build -t cloud-ready-api:${IMAGE_TAG} .
            """
          }
        }
      }
    }

    stage('Security Scan - Trivy') {
      steps {
        script {
          sh '''
            echo "Scanning Docker image with Trivy..."
            trivy image --exit-code 1 --severity HIGH,CRITICAL cloud-ready-api:${BUILD_NUMBER}
          '''
        }
      }
    }

    stage('Push to ECR') {
      steps {
        dir('app') {
          script {
            sh """
              aws ecr get-login-password --region ${AWS_DEFAULT_REGION} \
                | docker login --username AWS --password-stdin ${ECR_REPO}
              docker tag cloud-ready-api:${BUILD_NUMBER} ${ECR_REPO}:${BUILD_NUMBER}
              docker push ${ECR_REPO}:${BUILD_NUMBER}
            """
          }
        }
      }
    }

    stage('Deploy to EKS') {
      steps {
        script {
          sh '''
            aws eks update-kubeconfig --name cloud-ready-api-cluster --region us-east-1

            NEW_IMAGE="${ECR_REPO}:${BUILD_NUMBER}"
            sed -i "s|image: .*|image: ${NEW_IMAGE}|" k8s/deployment.yaml

            kubectl apply -f k8s/namespace.yaml
            kubectl apply -f k8s/deployment.yaml
            kubectl apply -f k8s/service.yaml
            kubectl apply -f k8s/ingress.yaml
          '''
        }
      }
    }
  }
}
