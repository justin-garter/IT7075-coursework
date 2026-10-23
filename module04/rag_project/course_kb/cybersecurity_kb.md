# Network Security Fundamentals
Network security protects data as it moves across an organization's infrastructure. Core controls include firewalls that filter traffic according to rules, network segmentation that isolates sensitive systems into separate zones, and virtual private networks (VPNs) that encrypt remote connections over untrusted networks. The defense-in-depth principle layers multiple independent controls so that the failure of any single mechanism does not compromise the entire network.

# Cryptography and Encryption
Cryptography secures information by transforming readable plaintext into unreadable ciphertext. Symmetric encryption such as AES uses one shared secret key for both encryption and decryption and is fast enough for bulk data. Asymmetric encryption such as RSA uses a public/private key pair, which enables secure key exchange and digital signatures. Hash functions like SHA-256 produce fixed-length fingerprints used to verify integrity; unlike encryption, hashing is one-way and cannot be reversed.

# Authentication and Access Control
Authentication verifies who a user is, while authorization determines what that user is allowed to do. Multi-factor authentication (MFA) strengthens login by combining something you know (a password), something you have (a hardware token or phone), and something you are (a biometric). The principle of least privilege grants each user only the access strictly needed for their job. Role-based access control (RBAC) assigns permissions to roles rather than individuals, which simplifies administration at scale.

# Malware and Threats
Malware is malicious software designed to damage systems or gain unauthorized access. Viruses attach themselves to legitimate files, worms self-propagate across networks without user action, and trojans disguise themselves as benign programs. Ransomware encrypts a victim's files and demands payment for the decryption key. Modern endpoint detection and response (EDR) tools use behavioral analysis to catch novel malware that traditional signature-based antivirus would miss.

# Social Engineering
Social engineering attacks manipulate people rather than exploiting technical flaws. Phishing emails impersonate trusted senders to trick victims into revealing credentials, spear phishing targets specific individuals with personalized lures, and pretexting invents a believable scenario to extract sensitive information. Because these attacks exploit human psychology rather than software bugs, technical controls alone are insufficient, and regular security-awareness training becomes a critical line of defense.

# Zero Trust Architecture
Zero trust abandons the old assumption that everything inside the network perimeter can be trusted. Its guiding motto is "never trust, always verify." Every request is authenticated, authorized, and encrypted regardless of whether it originates inside or outside the network. Micro-segmentation limits an attacker's lateral movement, and continuous verification repeatedly re-evaluates trust based on device posture, user behavior, and context throughout a session rather than only at login.

# Intrusion Detection and Prevention
An intrusion detection system (IDS) monitors network or host activity and raises alerts on suspicious behavior, while an intrusion prevention system (IPS) goes further and actively blocks malicious traffic. Signature-based detection matches activity against a database of known attack patterns, whereas anomaly-based detection flags deviations from a learned baseline of normal behavior. Anomaly detection can catch previously unseen attacks but tends to generate more false positives that analysts must triage.

# Security Operations Center
A Security Operations Center (SOC) is the team and facility responsible for continuous monitoring and defense of an organization. Analysts rely on a Security Information and Event Management (SIEM) platform to aggregate logs from across the enterprise, correlate related events, and surface prioritized alerts. SOC effectiveness is commonly measured by the mean time to detect (MTTD) and the mean time to respond (MTTR) to security incidents.

# Incident Response
Incident response is the structured process organizations follow when a security breach occurs. The widely adopted NIST framework defines four phases: preparation; detection and analysis; containment, eradication, and recovery; and post-incident activity. Containment isolates affected systems to stop the threat from spreading, eradication removes the malicious presence, and recovery restores normal operations. A post-incident review then captures lessons learned so future responses improve.

# Cloud Security
Cloud security operates under a shared responsibility model: the cloud provider secures the underlying infrastructure, while the customer remains responsible for securing their own data, identities, and configurations. Misconfigured storage buckets and overly permissive identity policies are among the leading causes of cloud data breaches. Cloud security posture management (CSPM) tools continuously audit configurations against best practices and flag risky settings before attackers can exploit them.
