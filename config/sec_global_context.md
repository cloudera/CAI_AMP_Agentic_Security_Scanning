# OWASP Top 10 (2021)

The [OWASP Top 10](https://owasp.org/www-project-top-ten/) is a standard awareness document for developers and web application security. It represents a broad consensus about the most critical security risks to web applications.

## Top 10 List

1. **A01:2021 – Broken Access Control**
2. **A02:2021 – Cryptographic Failures**
3. **A03:2021 – Injection**
4. **A04:2021 – Insecure Design**
5. **A05:2021 – Security Misconfiguration**
6. **A06:2021 – Vulnerable and Outdated Components**
7. **A07:2021 – Identification and Authentication Failures**
8. **A08:2021 – Software and Data Integrity Failures**
9. **A09:2021 – Security Logging and Monitoring Failures**
10. **A10:2021 – Server-Side Request Forgery (SSRF)**

---

## Details

### **A01:2021 – Broken Access Control**
Access control enforces policy such that users cannot act outside of their intended permissions. Failures typically lead to unauthorized information disclosure, modification, or destruction of all data or performing a business function outside the user's limits.

**How to Prevent:**
- Deny by default except for public resources
- Implement access control mechanisms once and re-use them
- Log access control failures and alert admins
- Rate limit API and controller access
- Invalidate session identifiers after logout

### **A02:2021 – Cryptographic Failures**
Focuses on failures related to cryptography (previously known as Sensitive Data Exposure). This includes weak or outdated cryptography, missing encryption, and improper key management.

**How to Prevent:**
- Use strong, up-to-date cryptographic algorithms
- Enforce encryption in transit and at rest
- Properly manage and rotate keys
- Avoid deprecated protocols and hash functions

### **A03:2021 – Injection**
Injection flaws, such as SQL, NoSQL, OS, and LDAP injection, occur when untrusted data is sent to an interpreter as part of a command or query.

**How to Prevent:**
- Use parameterized queries and safe APIs
- Validate and sanitize all user inputs
- Escape special characters
- Use ORM tools where possible

### **A04:2021 – Insecure Design**
Covers risks related to missing or ineffective security controls in the design phase.

**How to Prevent:**
- Integrate secure design patterns
- Use threat modeling
- Write unit and integration tests for critical flows
- Segregate tenants and layers by design

### **A05:2021 – Security Misconfiguration**
Covers improper configuration of security controls or default settings.

**How to Prevent:**
- Harden all environments
- Remove unused features and accounts
- Review and update configurations regularly
- Automate configuration checks

### **A06:2021 – Vulnerable and Outdated Components**
Using components with known vulnerabilities can compromise application security.

**How to Prevent:**
- Maintain an inventory of components
- Monitor for vulnerabilities and apply patches
- Remove unused dependencies
- Use official sources for components

### **A07:2021 – Identification and Authentication Failures**
Covers failures in authentication and session management.

**How to Prevent:**
- Implement multi-factor authentication
- Avoid default credentials
- Enforce strong password policies
- Invalidate sessions after logout

### **A08:2021 – Software and Data Integrity Failures**
Relates to code and infrastructure that does not protect against integrity violations, such as insecure CI/CD pipelines or untrusted updates.

**How to Prevent:**
- Use digital signatures for updates
- Secure CI/CD pipelines
- Use trusted repositories
- Review code and configuration changes

### **A09:2021 – Security Logging and Monitoring Failures**
Without proper logging and monitoring, breaches cannot be detected.

**How to Prevent:**
- Log all critical events
- Monitor logs for suspicious activity
- Establish incident response plans
- Use log management solutions

### **A10:2021 – Server-Side Request Forgery (SSRF)**
Occurs when a server fetches a remote resource without validating the user-supplied URL, allowing attackers to make requests to internal systems.

**How to Prevent:**
- Validate and sanitize all URLs
- Enforce allow-lists for destinations
- Segment network access
- Disable HTTP redirections

---
