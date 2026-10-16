                                                    
                                 
 
                                                       
                                                          
                                                        

import secrets

from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone

from .models import EmailOTP


                                                
                                                      
def make_code():
    number = secrets.randbelow(1000000)
    return str(number).zfill(6)


                                                                           
def mask_email(email):
    if '@' not in email:
        return email
    name, domain = email.split('@', 1)
    return name[0] + '*' * (len(name) - 1) + '@' + domain


                                                          
def is_expired(otp):
    age = timezone.now() - otp.created_at
    return age.total_seconds() > settings.OTP_EXPIRY_MINUTES * 60


                                                                          
                                            
def resend_wait_seconds(otp):
    age = (timezone.now() - otp.created_at).total_seconds()
    wait = settings.OTP_RESEND_SECONDS - age
    if wait <= 0:
        return 0
    return int(wait) + 1


                                                          
                                                              
def send_new_otp(user):
    code = make_code()

                                                                        
    EmailOTP.objects.update_or_create(
        user=user,
        defaults={
            'code_hash': make_password(code),
            'created_at': timezone.now(),
            'attempts': 0,
        }
    )

    context = {
        'name': user.first_name or user.username,
        'code': code,
        'minutes': settings.OTP_EXPIRY_MINUTES,
    }
    text_body = render_to_string('accounts/email/otp_email.txt', context)
    html_body = render_to_string('accounts/email/otp_email.html', context)

    message = EmailMultiAlternatives(
        subject='Your E-Commerce Shop verification code',
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, 'text/html')

    try:
                                                                           
                                                              
        sent_count = message.send(fail_silently=False)
        if sent_count != 1:
            print('Could not send OTP email: the email backend sent 0 messages.')
            return False
    except Exception as error:
                                                                            
                                                                         
        print('Could not send OTP email:', error)
        return False

    return True


                                   
                                         
def check_otp(otp, typed_code):
    if is_expired(otp):
        return False, 'This code has expired. Please request a new one.'

    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        return False, 'Too many wrong attempts. Please request a new code.'

    if not check_password(typed_code, otp.code_hash):
        otp.attempts += 1
        otp.save(update_fields=['attempts'])

        left = settings.OTP_MAX_ATTEMPTS - otp.attempts
        if left <= 0:
            return False, 'Too many wrong attempts. Please request a new code.'
        return False, f'Incorrect code. You have {left} attempt(s) left.'

    return True, ''
