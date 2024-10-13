from django.core.mail import EmailMessage

class Utils:
    @staticmethod
    def send_email(data):
        email = EmailMessage(
            subject=data['email_subject'],
            body=data['body'],
            from_email=os.getenv('EMAIL_FROM'),
            to=[data['to_email']]
        )
        email.send()
