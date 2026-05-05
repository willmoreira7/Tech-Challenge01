data "aws_vpc" "this" {
  default = true
}

data "aws_subnets" "this" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.this.id]
  }
}

resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg"
  description = "Allow HTTP and HTTPS inbound for ALB"
  vpc_id      = data.aws_vpc.this.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-alb-sg" })
}

resource "aws_lb" "this" {
  name               = "${var.project_name}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = data.aws_subnets.this.ids

  tags = merge(var.tags, { Name = "${var.project_name}-alb" })
}

# --- Target Groups ---

resource "aws_lb_target_group" "flask" {
  name     = "${var.project_name}-api-tg"
  port     = var.flask_port
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.this.id

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = merge(var.tags, { Name = "${var.project_name}-api-tg" })
}

resource "aws_lb_target_group" "mlflow" {
  name     = "${var.project_name}-ml-tg"
  port     = var.mlflow_port
  protocol = "HTTP"
  vpc_id   = data.aws_vpc.this.id

  health_check {
    path                = "/mlflow/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    interval            = 30
    timeout             = 5
  }

  tags = merge(var.tags, { Name = "${var.project_name}-ml-tg" })
}

resource "aws_lb_target_group_attachment" "flask" {
  target_group_arn = aws_lb_target_group.flask.arn
  target_id        = var.instance_id
  port             = var.flask_port
}

resource "aws_lb_target_group_attachment" "mlflow" {
  target_group_arn = aws_lb_target_group.mlflow.arn
  target_id        = var.instance_id
  port             = var.mlflow_port
}

# --- Listeners ---

# HTTP: redirect all to HTTPS
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# HTTPS: default → Flask
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = var.acm_certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }
}

# Host-based rule: api.pocsarcotech.com → Flask
resource "aws_lb_listener_rule" "flask" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.flask.arn
  }

  condition {
    host_header {
      values = [var.flask_domain]
    }
  }
}

# Host-based rule: mlflow.pocsarcotech.com → MLflow
resource "aws_lb_listener_rule" "mlflow" {
  listener_arn = aws_lb_listener.https.arn
  priority     = 20

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mlflow.arn
  }

  condition {
    host_header {
      values = [var.mlflow_domain]
    }
  }
}
