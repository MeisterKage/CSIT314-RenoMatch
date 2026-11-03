# US-05 diagram text (extracted from US-05_diagrams.drawio)

Every name below is the exact spelling the code must use.

```
=== US-05 Class Diagram
[box] «boundary» | ResetPasswordPage
[box] - controller: ResetPasswordController
[box] + displayForgotPasswordForm(): void | + displayResetForm(): void | + displayMessage(): void | + displayResetSuccess(): void
[box] «control» | ResetPasswordController
[box] - entity: UserAccountEntity
[box] + requestPasswordReset(email: String): boolean | + resetPassword(token: String, newPassword: String): boolean | - sendResetLink(email: String): void | - validatePassword(newPassword: String): boolean
[box] «entity» | UserAccountEntity
[box] - userId: int | - email: String | - passwordHash: String | - resetToken: String | - tokenExpiry: DateTime
[box] + requestPasswordReset(email: String): boolean | + resetPassword(token: String, newPassword: String): boolean
=== US-05 Sequence Diagram
[box] Registered User
[box] : ResetPasswordPage
[box] : ResetPasswordController
[box] : UserAccountEntity
[box] alt
[box] alt
[box] alt
[box] [email registered]
[box] [4a. email not registered: no email sent]
[box] [password valid]
[box] [9b. password breaks rules or does not match]
[box] [result = true]
[box] [9a. token invalid or expired]
[edge] 1: enter email, click "Send Reset Link"
[edge] 1.1: requestPasswordReset(email)
[edge] 1.1.1: requestPasswordReset(email)
[edge] emailFound
[box] 1.1.2: sendResetLink(email)
[edge] true
[box] 1.2: displayMessage()
[edge] true
[box] 1.3: displayMessage()
[edge] 2: open reset link, enter new password
[edge] 2.1: resetPassword(token, newPassword)
[box] 2.1.1: validatePassword(newPassword)
[edge] 2.1.2: resetPassword(token, newPassword)
[edge] result
[edge] result
[box] 2.2: displayResetSuccess()
[box] 2.3: displayMessage()
[edge] false
[box] 2.4: displayMessage()
```
