# backend/crm/signals.py
import logging
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django_rest_passwordreset.signals import reset_password_token_created, post_password_reset

logger = logging.getLogger('sgfs_app')

@receiver(post_password_reset)
def password_was_reset(sender, user, *args, **kwargs):
    """
    Intercepta o evento após a senha ser redefinida para garantir que o usuário
    seja salvo corretamente.
    """
    logger.info(f"--- SINAL 'post_password_reset' RECEBIDO ---")
    try:
        # A biblioteca pode não salvar o usuário após set_password.
        # Esta linha força o salvamento para garantir a consistência da hash.
        user.save()
        logger.info(f"Usuário {user.email} salvo com sucesso após a redefinição de senha.")
    except Exception as e:
        logger.error(f"FALHA ao salvar o usuário {user.email} após redefinir a senha: {e}", exc_info=True)

    logger.info(f"--- FIM DO SINAL 'post_password_reset' ---")

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    user = reset_password_token.user
    token = reset_password_token.key

    logger.info(f"--- INICIANDO ENVIO MANUAL DE E-MAIL DE RECUPERAÇÃO ---")
    logger.info(f"Sinal recebido para o usuário: {user.email}")

    try:
        # URL base do seu site
        base_url = "https://fundosocial.mogidascruzes.sp.gov.br"
        
        context = {
            'user_name': user.first_name or user.username,
            'reset_url': f"{base_url}/reset-password/{token}",
            # CORREÇÃO: Construindo a URL do logo de forma explícita e completa
            'logo_url': f"{base_url}/static/crm/images/logo_sgfs.png" 
        }

        html_content = render_to_string('crm/password_reset_email.html', context)
        text_content = f"Olá {context['user_name']},\n\nPara redefinir sua senha, acesse o seguinte link:\n{context['reset_url']}"

        email = EmailMultiAlternatives(
            "Recuperação de Senha - SGFS",
            text_content,
            None,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
        
        logger.info(f"E-MAIL DE RECUPERAÇÃO ENVIADO COM SUCESSO para {user.email}.")

    except Exception as e:
        logger.error(f"FALHA CRÍTICA AO ENVIAR E-MAIL DE RECUPERAÇÃO: {e}", exc_info=True)
    
    logger.info(f"--- FIM DO PROCESSO DE ENVIO MANUAL ---")