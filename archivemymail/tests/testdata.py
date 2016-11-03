import email

test_message1 = email.message.Message()
test_message1['Subject'] = 'Test subject'
test_message1['From'] = 'test@example.com'
test_message1['To'] = 'recip@example.com'
test_message1['Date'] = '01-Jan-2010'
test_message1.set_payload('This is a test message\n')

test_message2 = email.message.Message()
test_message2['Subject'] = "GewSt:=?UTF-8?B?IFdlZ2ZhbGwgZGVyIFZvcmzDpHVmaWdrZWl0?="
test_message2['From'] = 'John Doe <j@example.org>'
test_message2['To'] = 'bill@example.org'
test_message2.set_payload("Another test\n")
