import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MailSender:
    def send(self, reciever_mail, auctionNumber, auctionData, michrazim_url, log):
        # Email details
        sender_email = "rashutm24@gmail.com"
        password = "sqyp kgpd istg utph"  # Use an app-specific password

        # Create the email content
        subject = "הודעה ממערכת מכרזים"
        #body = f"מכרז {auctionNumber} נפתח להצעות"
        numerator, denominator = map(str, auctionNumber.split('/'))
        auctionNumberFormatted = denominator.strip() + numerator.strip().zfill(4)
        
        body = f"""
        <html>
        <body>
            <table border="0" dir="rtl">
                <tr>
                    <td style='text-align: right' colspan=2><b>מכרז {auctionNumber} נפתח להצעות</b></td>
                </tr>
               <tr><td style='color:blue;text-align: right'>סוג מכרז:</td><td style='text-align: right'>{auctionData['auction_type']}</td></tr>
               <tr><td style='color:blue;text-align: right'>ייעוד:</td><td style='text-align: right'>{auctionData['vocation']}</td></tr>
               <tr><td style='color:blue;text-align: right'>מיקום:</td><td style='text-align: right'>{auctionData['city']}</td></tr>
               <tr><td style='color:blue;text-align: right'>יחידות:</td><td style='text-align: right'>{auctionData['numUnits']}</td></tr>
               <tr><td style='color:blue;text-align: right'>פתיחה:</td><td style='text-align: right'>{auctionData['openDate']}</td></tr>
               <tr><td style='color:blue;text-align: right'>מועד אחרון:</td><td style='text-align: right'>{auctionData['lastDate']}</td></tr>
               <tr><td style='color:blue;text-align: right'>לינק:</td><td style='text-align: right'>{michrazim_url}/michraz/{auctionNumberFormatted}</td></tr>


            </table>
        </body>
        </html>
        """



        # Create a MIMEText object
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = reciever_mail
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        # Connect to the Gmail SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, password)
            server.sendmail(sender_email, reciever_mail, msg.as_string())
            log(f"mail sent {auctionNumber}")

        print("Email sent successfully!")
