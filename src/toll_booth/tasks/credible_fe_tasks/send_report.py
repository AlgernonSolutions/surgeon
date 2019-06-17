from aws_xray_sdk.core import xray_recorder


def _send_by_ses(**kwargs):
    import boto3

    client = boto3.client('ses')
    recipients = kwargs['recipients']
    html_body, text_body = kwargs['html_body'], kwargs['text_body']
    subject_line = kwargs['subject_line']

    response = client.send_email(
        Source='algernon@algernon.solutions',
        Destination={
            'ToAddresses': [x['email_address'] for x in recipients]
        },
        Message={
            'Subject': {'Data': subject_line},
            'Body': {
                'Text': {'Data': text_body},
                'Html': {'Data': html_body}
            }
        },
        ReplyToAddresses=['algernon@algernon.solutions']
    )
    return response


@xray_recorder.capture('send_report')
def send_report(**kwargs):
    from toll_booth.obj import StaticJson

    report_recipients = StaticJson.for_report_recipients(**kwargs).stored_asset
    download_link = kwargs['download_link']
    subject_line = 'Algernon Solutions Clinical Intelligence Report'
    text_body = f''' 
        You are receiving this email because you have requested to have routine reports sent to you through the 
        Algernon Clinical Intelligence Platform. 
        The requested report can be downloaded from the included link. To secure the information contained within, 
        the link will expire in {download_link.expiration_hours} hours. 
        I hope this report brings you joy and the everlasting delights of a cold data set.

        {str(download_link)}

        - Algernon

        This communication, download link, and any attachment may contain information, which is sensitive, 
        confidential and/or privileged, covered under HIPAA and is intended for use only by the addressee(s) 
        indicated above. If you are not the intended recipient, please be advised that any disclosure, copying, 
        distribution, or use of the contents of this information is strictly prohibited. If you have received this 
        communication in error, please notify the sender immediately and destroy all copies of the original 
        transmission. 
    '''
    html_body = f'''
       <!DOCTYPE html>
        <html lang="en" xmlns="http://www.w3.org/1999/html" xmlns="http://www.w3.org/1999/html">
            <head>
                <meta charset="UTF-8">
                <title>Algernon Clinical Intelligence Report</title>
                <style>

                    .container {{
                        position: relative;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <p>You are receiving this email because you have requested to have routine reports sent to you 
                through the Algernon Clinical Intelligence Platform.</p> 
                <p>The requested report can be downloaded from the included link. To secure the information contained 
                within, the link will expire in {download_link.expiration_hours} hours.</p> 
                <p>I hope this report brings you joy and the everlasting delights of a cold data set.</p>
                <h4><a href="{str(download_link)}">Download Report</a></h4>
                <p> - Algernon </p>
                <h5>
                    This communication, download link, and any attachment may contain information, which is 
                    sensitive, confidential and/or privileged, covered under HIPAA and is intended for use only by 
                    the addressee(s) indicated above.<br/> 
                    If you are not the intended recipient, please be advised that any disclosure, copying, 
                    distribution, or use of the contents of this information is strictly prohibited.<br/> 
                    If you have received this communication in error, please notify the sender immediately and 
                    destroy all copies of the original transmission.<br/> 
                </h5>
            </body>
        </html>
    '''

    response = _send_by_ses(recipients=report_recipients['recipients'], subject_line=subject_line, text_body=text_body,
                            html_body=html_body, **kwargs)
    return {'message_id': response['MessageId'], 'text_body': text_body, 'html_body': html_body}
