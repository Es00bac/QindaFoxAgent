"""Synthetic benchmark inputs. Expected answers never enter the agent observation."""
import random

GROUPS = {
'billing': [
('normal','We were charged twice for the same monthly subscription. Please reverse the duplicate charge.'),
('normal','Our paid invoice still shows overdue and the account has been suspended. Please reconcile the payment.'),
('low','Please send a PDF copy of the invoice from last month for our records. Everything is working.'),
('normal','The card update page rejects our replacement company card, so we cannot renew the subscription.'),
('low','We need the company address corrected on the next invoice. This is not blocking anything.'),
('normal','We upgraded yesterday but the invoice charged us for two different plans. Please fix the charge.'),
('low','Can you explain the tax line on our latest invoice? We are not disputing it and there is no deadline.'),
('normal','Our cancellation was confirmed but another renewal payment was taken. Please review the charge.')],
'access': [
('critical','An unknown person changed our administrator email and is actively logging in. We believe the account is compromised.'),
('normal','My password reset link has expired three times and I cannot sign in to my own account.'),
('normal','I replaced my phone and lost my authenticator codes. I cannot pass the two-factor login screen.'),
('low','I would like instructions for enabling two-factor authentication. My account works normally.'),
('normal','Our new colleague accepted an invitation but receives access denied when opening the workspace.'),
('critical','We found an unauthorized administrator session and the attacker is changing account permissions right now.'),
('low','How can I view the devices currently signed into my account? There is no suspected breach.'),
('normal','The single sign-on login loops back to the sign-in page for my user. Other team members can sign in.')],
'incident': [
('critical','All production API requests return 503. Every customer is unable to use the service. This is a complete outage.'),
('critical','Saved customer records are disappearing continuously from our production database. Data loss is ongoing.'),
('normal','The CSV export crashes on one specific report. The rest of the application and other exports work.'),
('normal','Uploading a valid PNG always shows an internal server error in our project. Other features are working.'),
('critical','The entire production website has been unavailable for twenty minutes and all users are affected.'),
('normal','The weekly report produces the wrong total after I apply a date filter. This looks like a calculation bug.'),
('low','There is a cosmetic alignment bug in the footer. All workflows work and there is no urgency.'),
('critical','The production sync service is actively deleting existing files unexpectedly. Please stop the ongoing data loss.')],
'feature': [
('low','Please consider adding a dark theme in a future release. The current app works fine.'),
('low','We would love a native calendar integration as a new feature. There is no deadline or current blocker.'),
('low','Could a future version support recurring project templates? This is an enhancement idea.'),
('low','Feature suggestion: let us pin favorite reports to the dashboard. Nothing is broken.'),
('low','Please add the ability to customize chart colors in a later release. This is optional for us.'),
('low','We would like a new public API endpoint for custom tags someday. Our current workflow is working.'),
('low','An offline reading mode would be useful for travel. Please consider it for the product roadmap.'),
('low','Could you add keyboard shortcuts for switching between projects? This is a nice-to-have feature.')],
'howto': [
('low','Where can I find the existing user guide for creating a project? I am learning the product.'),
('low','Please explain how to use the existing date filter on the dashboard. Nothing is failing.'),
('low','What are the steps to export an existing report as PDF? I only need instructions.'),
('low','How do I rename a project using the current interface? This is a routine usage question.'),
('low','I need instructions for scheduling an existing weekly summary. The feature already exists.'),
('low','Where is the documentation for the existing webhook setup? I am exploring it for a future project.'),
('low','How do I change the language displayed in my personal preferences? Everything is working normally.'),
('low','Please point me to the tutorial for organizing existing reports into folders. No issue or deadline.')]
}
TEAM = {'billing':'accounts','access':'identity','incident':'engineering','feature':'product','howto':'enablement'}
TICKETS = [{'id':f'RQ-{1001+i}', 'text':text,'expected':{'category':category,'urgency':urgency,'team':TEAM[category]}} for i,(category,urgency,text) in enumerate((c,u,t) for c,items in GROUPS.items() for u,t in items)]
random.Random(26).shuffle(TICKETS)
