# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please follow these steps:

### 1. **DO NOT** create a public GitHub issue
Security vulnerabilities should be reported privately to prevent exploitation.

### 2. Email the security team
Send details to: [security@shapeshift.com](mailto:security@shapeshift.com)

### 3. Include in your report:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)
- Your contact information

### 4. Response timeline
- **Initial response**: Within 48 hours
- **Status update**: Within 1 week
- **Resolution**: Depends on severity and complexity

## Security Best Practices

### For Users
- Keep your API keys secure and never commit them to version control
- Use environment variables for sensitive configuration
- Regularly rotate your API keys
- Monitor your API usage for unusual activity

### For Developers
- Never hardcode API keys or secrets
- Use `.env` files for local development (not committed to git)
- Validate all input data, especially blockchain addresses
- Implement proper rate limiting and error handling
- Use HTTPS for all external API calls

## Disclosure Policy

- Security vulnerabilities will be disclosed after they are fixed
- A security advisory will be published with:
  - Description of the vulnerability
  - Affected versions
  - Upgrade instructions
  - Credits for responsible disclosure

## Responsible Disclosure

We appreciate security researchers who:
- Report vulnerabilities privately
- Allow reasonable time for fixes
- Avoid exploiting vulnerabilities
- Follow responsible disclosure practices

Thank you for helping keep our users safe!

