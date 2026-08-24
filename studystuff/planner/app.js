'use strict';

/* ============================================================
   CONSTANTS
   ============================================================ */
const STORAGE_KEY = "securityStudyPlanner:v1";
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const REVIEW_INTERVALS = [1, 3, 7, 14, 30];

/* ============================================================
   PLAN DATA  (exact source wording)
   ============================================================ */
const PLAN = [
  week(1, "Learning + Interviewing Tips", "Build study habits and the interview communication loop.", [
    t("Learning how to learn", "low", 45, "Use active recall, spaced repetition, and short summaries instead of passive rereading.", ["Guess before checking answers", "Review terms throughout the day", "Use paper when distraction is a problem"], "Create a one-page study routine."),
    t("Track concepts", "low", 30, "Move terms through To learn, Revising, and Done.", ["One term per note", "Move hard topics first", "Update the board every few days"], "List 20 concepts you cannot explain yet."),
    t("Review concepts", "medium", 35, "Practice recall before lookup.", ["Ask what a term means before searching", "Explain in your own words", "Use spaced repetition"], "Explain five weak terms without notes."),
    t("Clarifying questions", "low", 30, "Vague interview questions invite questions.", ["Repeat the question", "Ask constraints", "Write assumptions"], "Restate three prompts before answering."),
    t("Think aloud", "medium", 45, "Make your reasoning visible to the interviewer.", ["Narrate alternatives", "Say when uncertain", "Use first principles"], "Record a two-minute explanation."),
    t("Practice interviews", "medium", 60, "Get comfortable with hard, unfamiliar questions.", ["Ask peers for difficult prompts", "Speak all relevant details", "Use pseudocode and tests"], "Schedule one mock interview.")
  ]),
  week(2, "Networking", "Core protocols, ports, traffic behavior, and network tools.", [
    t("OSI model", "medium", 45, "Map protocols to application, transport, network, datalink, and physical layers.", ["Layer 7 includes HTTP and APIs", "Layer 4 is TCP/UDP", "Layer 3 is routing"], "Place DNS, TCP, IP, and Ethernet on the model."),
    t("DNS", "high", 60, "Study DNS resolution, records, caching, logs, sinkholes, and reverse lookup.", ["Usually UDP 53", "PTR records support reverse lookup", "Raw IPs skip DNS logs"], "Trace a domain lookup step by step."),
    t("DNS exfiltration", "high", 45, "Data can be encoded into subdomains and sent through DNS queries.", ["Watch long or high-entropy queries", "HTTP logs may miss it", "Sinkholes can disrupt it"], "Design two DNS exfil detections."),
    t("DHCP and ARP", "medium", 45, "Understand dynamic addressing and IP-to-MAC mapping.", ["DHCPDISCOVER to DHCPACK", "ARP checks cache first", "ARP spoofing enables interception"], "Draw DHCP and ARP flows."),
    t("TCP, UDP, and ICMP", "high", 55, "Compare reliability, loss behavior, and diagnostic usage.", ["TCP throttles on loss", "UDP avoids TCP-style reliability", "ICMP supports ping and traceroute"], "Explain why streaming affects TCP traffic."),
    t("SSL/TLS", "very-high", 75, "Understand handshakes, CAs, trust stores, encryption, signing, and bugs.", ["Commonly port 443", "Asymmetric exchange for symmetric keys", "Review POODLE, BEAST, CRIME, BREACH, Heartbleed"], "Whiteboard a TLS handshake."),
    t("Service ports", "medium", 40, "Memorize common ports and port ranges.", ["HTTP 80, HTTPS 443, SSH 22", "SMTP 25/587/465", "0-1023 reserved"], "Create a quick port quiz."),
    t("Traffic tools", "medium", 45, "Know Nmap, traceroute, Wireshark, tcpdump, and Burp Suite.", ["Nmap scans services", "tcpdump and Wireshark inspect packets", "Burp inspects web traffic"], "Map each tool to a scenario.")
  ]),
  week(3, "Web Application", "Browser controls, HTTP, and common web vulnerabilities.", [
    t("Same origin policy and CORS", "high", 55, "Understand origin restrictions and controlled cross-origin access.", ["CORS uses response headers", "Preflight checks permissions", "Cookies affect risk"], "Compare simple and preflighted requests."),
    t("HSTS and certificate transparency", "medium", 35, "Study HTTPS enforcement and public certificate logs.", ["HSTS forces HTTPS", "Certificate transparency reveals issued certs", "HPKP is deprecated"], "Explain why CT helps defenders."),
    t("Cookies and CSRF", "high", 55, "Connect cookie behavior to cross-site request forgery.", ["HttpOnly blocks JS access", "SameSite helps", "CSRF abuses ambient auth"], "Describe a CSRF against settings."),
    t("XSS", "very-high", 70, "Differentiate reflected, persistent, and DOM-based XSS.", ["Reflected returns payload immediately", "Stored persists on server", "DOM XSS is client-side"], "Explain output encoding."),
    t("SQL injection", "very-high", 70, "Study blind, time-based, error-based, and union-based SQLi.", ["Blind infers without direct output", "Time-based uses delay", "Parameterized queries mitigate"], "Explain why prepared statements work."),
    t("SSRF, LFI, RFI", "high", 60, "Recognize server-side request and file inclusion classes.", ["SSRF targets internal or metadata services", "LFI reads local files", "RFI loads remote files"], "List cloud metadata SSRF risks."),
    t("Web tools", "medium", 45, "Know Burp Suite, scanners, SQLmap, API review, and redirect testing.", ["Burp modifies HTTP", "SQLmap automates SQLi testing", "APIs may leak or accept sensitive data"], "Pick a tool for three web tests.")
  ]),
  week(4, "Infrastructure and Cloud Virtualisation", "Isolation boundaries, cloud movement, and service identities.", [
    t("Hypervisors", "high", 50, "Study VM isolation and hyperjacking risk.", ["Host vs guest boundary", "Hypervisor compromise is high impact", "Patching matters"], "Explain why hypervisor compromise is severe."),
    t("Containers, VMs, clusters", "medium", 45, "Compare isolation and operations tradeoffs.", ["Containers share kernels", "VMs isolate more strongly", "Clusters add orchestration risk"], "Compare container and VM escapes."),
    t("Escaping techniques", "high", 50, "Learn common ways workloads cross boundaries.", ["Runtime bugs", "Host mounts", "Network paths from workloads"], "List three container boundaries to audit."),
    t("Cloud service accounts", "high", 60, "Understand lateral movement through automation identities.", ["Restrict privileges", "Avoid long-lived keys", "Watch ActAs-like permission chains"], "Describe a least-privilege service account."),
    t("Side-channel attacks", "high", 50, "Review Spectre, Meltdown, and shared-infrastructure leakage.", ["Indirect signals leak information", "Hardware and software mitigations matter", "Cloud multi-tenancy increases impact"], "Summarize why side channels matter."),
    t("BeyondCorp and Log4j", "medium", 45, "Connect zero-trust ideas with widespread dependency response.", ["Trust host and identity, not network location", "Asset inventory drives Log4j response", "Exposure reduction matters"], "Explain how inventory changes response speed.")
  ]),
  week(5, "OS Implementation and Systems", "Privilege, memory safety, platform internals, and local artifacts.", [
    t("Privilege escalation", "high", 55, "Move from low privilege to higher privilege through bugs, credentials, or misconfiguration.", ["Least privilege reduces impact", "Patch local bugs", "Audit weak permissions"], "Compare initial access and privilege escalation."),
    t("Buffer overflows and ROP", "very-high", 75, "Understand memory corruption and code-reuse exploitation concepts.", ["Overwrites redirect execution", "ROP chains existing code", "DEP and ASLR raise the bar"], "Explain a stack overflow conceptually."),
    t("RCE and shells", "high", 55, "Remote execution can lead to bind or reverse shells.", ["Execution context shapes impact", "Reverse shells call out", "Bind shells listen on target"], "Compare bind and reverse shells."),
    t("Windows internals", "high", 60, "Review Registry, Group Policy, AD, Kerberos, SMB, BloodHound, and Mimikatz terms.", ["AD centralizes identity", "SMB supports file/service access", "BloodHound maps relationships"], "Explain why AD graphs matter."),
    t("Unix-like systems", "high", 60, "Study permissions, SELinux, MAC/DAC, /proc, /tmp, /shadow, and LDAP.", ["/tmp may hold executable code", "/proc exposes process data", "SELinux is MAC"], "Compare MAC and DAC."),
    t("Local databases", "medium", 35, "SQLite stores can matter for apps and forensics.", ["Messaging apps may use SQLite", "Deleted data may remain", "Schemas guide recovery"], "Name artifacts in an app database."),
    t("macOS security", "medium", 35, "Review Gotofail, MacSweeper, and platform-specific research.", ["macOS has unique security models", "Historical cases teach validation errors", "Research current vulnerabilities"], "Summarize one macOS bug.")
  ]),
  week(6, "Mitigations", "Controls that reduce exploitability and impact.", [
    t("Patching", "medium", 35, "Remove known vulnerabilities through prioritized updates.", ["Inventory matters", "Prioritize exposed critical systems", "Verify deployment"], "Make a patch triage checklist."),
    t("DEP and ASLR", "high", 55, "Memory mitigations make exploitation harder.", ["DEP blocks execution from data pages", "ASLR randomizes addresses", "Bypasses often chain bugs"], "Explain how DEP and ASLR complement each other."),
    t("Least privilege", "medium", 40, "Grant only the access needed.", ["Limit admin tokens", "Scope service accounts", "Review privileges"], "Reduce one fictional role policy."),
    t("Code signing", "medium", 35, "Verify software origin and integrity.", ["Kernel-mode signing raises the bar", "Trust chains matter", "Signing does not guarantee safe behavior"], "Explain signing vs encryption."),
    t("MACs and ACLs", "medium", 40, "Compare mandatory access controls and access control lists.", ["ACLs map access", "MAC enforces system policy", "SELinux is an example"], "Give one example of each."),
    t("Insecure by exception", "medium", 35, "Improve the baseline while tracking necessary exceptions.", ["Do not block legitimate work blindly", "Document exceptions", "Review periodically"], "Draft exception review questions."),
    t("Do not blame the user", "low", 25, "Security should protect people and systems.", ["Design for real behavior", "Fix system causes", "Build trustworthy defaults"], "Rewrite one user-blaming control.")
  ]),
  week(7, "Cryptography", "Purposes, primitives, protocols, and common confusion.", [
    t("Encryption vs encoding vs hashing vs obfuscation vs signing", "very-high", 75, "Distinguish secrecy, compatibility, integrity, hindrance, and authenticity.", ["Encryption is for secrecy", "Encoding is for compatibility", "Hashing is for integrity", "Signing is for authenticity"], "Give one example for each."),
    t("Symmetric and asymmetric encryption", "high", 60, "Compare shared-key speed with public/private key trust.", ["Symmetric is fast", "Asymmetric is slower", "Protocols often combine both"], "Explain why TLS uses both."),
    t("RSA, AES, ECC, Chacha/Salsa", "high", 55, "Recognize common algorithms and their categories.", ["RSA and ECC are asymmetric", "AES and Chacha/Salsa are symmetric", "Choice depends on protocol"], "Sort algorithms into categories."),
    t("PKI", "very-high", 70, "Manage trust for public keys with CAs, certificates, and root stores.", ["CAs issue certificates", "Root stores anchor trust", "DH and ECDH exchange keys"], "Explain browser certificate trust."),
    t("Forward secrecy", "high", 55, "Preserve past session secrecy after later key compromise.", ["Use ephemeral keys", "Messaging may use Double Ratchet", "Rotate session keys"], "Explain with chat messages."),
    t("Ciphers and modes", "very-high", 70, "Compare block and stream ciphers and AES-GCM style modes.", ["Block ciphers use blocks", "Stream ciphers use keystreams", "Authenticated modes add integrity"], "Explain why modes matter."),
    t("MACs and HMAC", "high", 55, "Use keyed primitives for integrity and authenticity.", ["MACs require a shared secret", "HMAC combines a key and hash", "Hashes identify malware samples"], "Compare hash and HMAC."),
    t("Entropy and PRNGs", "high", 50, "Randomness quality affects cryptographic security.", ["Weak randomness breaks keys", "PRNGs expand seeds", "Entropy buffers can drain"], "Explain predictable token risk.")
  ]),
  week(8, "Authentication", "Certificates, tokens, sessions, protocols, and MFA.", [
    t("Certificates", "high", 50, "Know certificate contents, signing, and DigiNotar-style failures.", ["Bind identity to public key", "Signed by CA", "Trust can fail at scale"], "List expected cert fields."),
    t("TPM", "medium", 35, "Hardware-backed local storage for certs and auth data.", ["Protects device secrets", "Can support attestation", "Does not solve endpoint compromise"], "Explain TPM value."),
    t("OAuth bearer tokens", "high", 50, "Bearer tokens can be stolen and reused.", ["Possession is enough", "Scope and expiry matter", "Storage location matters"], "Limit token blast radius."),
    t("Auth cookies and sessions", "high", 50, "Compare client-side cookies and server-side session state.", ["Cookies carry identifiers or tokens", "Sessions support revocation", "Flags matter"], "Trace a login flow."),
    t("SAML, OpenID, Kerberos", "very-high", 70, "Review enterprise auth protocols and AD attack vocabulary.", ["SAML and OIDC support federation", "Kerberos uses tickets", "Gold/silver tickets and pass-the-hash matter"], "Compare a SAML assertion and Kerberos ticket."),
    t("Biometrics", "medium", 30, "Biometric identifiers cannot be rotated like passwords.", ["Convenient", "Hard to replace", "Recovery flows matter"], "List strengths and risks."),
    t("U2F and FIDO", "high", 45, "Hardware-backed authentication resists phishing.", ["Binds auth to origin", "YubiKeys are an example", "Stronger than SMS/TOTP against phishing"], "Explain U2F phishing resistance."),
    t("MFA comparison", "medium", 45, "Compare SMS, TOTP, push, biometrics, and hardware keys.", ["Phishing resistance varies", "Recovery can weaken systems", "Usability matters"], "Make an MFA comparison table.")
  ]),
  week(9, "Identity", "Authorization, service accounts, impersonation, and federation.", [
    t("ACLs", "medium", 35, "Control which authenticated users can access resources.", ["ACLs map subjects to permissions", "Review for excess access", "Authorization differs from authentication"], "Create a sample ACL."),
    t("Service accounts vs user accounts", "medium", 45, "Separate automation identity from human identity.", ["Service accounts run automation", "Restrict privileges", "Attackers abuse them in cloud"], "Compare lifecycle needs."),
    t("Exported account keys", "high", 45, "Long-lived keys can be copied and reused.", ["Rotate keys", "Prefer short-lived credentials", "Monitor key usage"], "Describe a key response plan."),
    t("Impersonation and ActAs", "high", 50, "Permission chains can let one identity become another.", ["ActAs grants can escalate", "JWTs carry delegated claims", "Graph permissions reveal paths"], "Sketch an impersonation attack path."),
    t("Federated identity", "medium", 40, "Trust one identity provider across services.", ["Reduces password sprawl", "Claim mapping matters", "Logs span systems"], "Name one federation misconfiguration risk.")
  ]),
  week(10, "Malware and Reversing", "Malware behavior, analysis, and reversing tools.", [
    t("Malware case studies", "high", 65, "Review Conficker, Morris worm, Zeus, Stuxnet, WannaCry, CookieMiner, and Sunburst.", ["Know propagation", "Know impact", "Know response lessons"], "Summarize three families."),
    t("C2, domain-flux, fast-flux", "high", 55, "Understand resilient command-and-control infrastructure.", ["Domain-flux changes domains", "Fast-flux changes IPs", "C2 may hide in common protocols"], "Design DNS detections."),
    t("Evasion techniques", "high", 60, "Review anti-sandbox, process hollowing, mutexes, polymorphism, and RAT features.", ["Anti-sandbox checks environment", "Process hollowing hides execution", "Mutex names can be indicators"], "Explain process hollowing."),
    t("Reversing tools", "high", 55, "Use IDA Pro, Ghidra, decompilers, and unique strings.", ["Strings reveal behavior", "Decompilers reconstruct logic", "Obfuscation slows analysis"], "List artifacts from a suspicious binary."),
    t("Static vs dynamic analysis", "high", 55, "Compare inspecting files to observing controlled execution.", ["Static avoids running code", "Dynamic reveals behavior", "Sandboxes can be detected"], "Create a safe analysis checklist."),
    t("YARA and malware signatures", "medium", 45, "Match suspicious strings or byte patterns in malware samples.", ["Rules balance specificity and coverage", "Hashes identify exact samples", "Strings can identify families"], "Draft a YARA rule idea.")
  ]),
  week(11, "Exploits", "Social, physical, and network attack categories.", [
    t("Social attacks", "medium", 50, "Study phishing, spear phishing, water holing, baiting, and tailgating.", ["Exploit trust", "Use cognitive biases", "Technical controls are not enough"], "Design a USB baiting defense."),
    t("Physical attacks", "high", 60, "Review disk access, boot media, keyloggers, jamming, hidden cameras, TPM, and TEMPEST.", ["Disk encryption matters", "Physical access changes assumptions", "Secure boot affects boot attacks"], "Explain disk encryption value."),
    t("Network attacks", "high", 60, "Use scanning, CVE lookup, interception, and unsecured information exposure.", ["Nmap discovers services", "Version numbers guide CVE research", "PKI affects interception"], "Describe a safe assessment workflow."),
    t("Exploit kits", "high", 45, "Automated exploit delivery through compromised or malicious pages.", ["Fingerprint browsers", "Bundle exploits", "Patch browsers and plugins"], "Explain drive-by downloads."),
    t("Bind and reverse shells", "high", 45, "Compare remote-control connection direction.", ["Bind listens on target", "Reverse connects outward", "Egress controls matter"], "Compare network implications."),
    t("Spoofing", "medium", 45, "Review email, IP, MAC, biometric, and ARP spoofing.", ["Fakes identity or origin", "Controls differ by layer", "Logs can mislead"], "Map spoofing types to mitigations."),
    t("Exploit tools", "medium", 40, "Know Metasploit, ExploitDB, Shodan, Google version lookup, and Hak5 tools.", ["Metasploit packages exploits", "ExploitDB catalogs public exploits", "Shodan finds exposed systems"], "Name a defensive Shodan use.")
  ]),
  week(12, "Attack Structure", "Describe attacks from reconnaissance through impact.", [
    t("Recon and resource development", "high", 55, "Use OSINT, Google dorking, Shodan, infrastructure, malware, and accounts.", ["Recon finds targets", "Resources prepare access", "Both can precede compromise"], "Walk through pre-attack preparation."),
    t("Initial access and execution", "high", 65, "Review phishing, hardware placement, supply chain, public app exploits, interpreters, WMI, and scheduled tasks.", ["Initial access creates foothold", "Execution runs code", "Interpreters are common"], "Map access methods to logs."),
    t("Persistence and privilege escalation", "high", 70, "Study accounts, startup scripts, launch agents, DLL side-loading, webshells, sudo, token theft, and IAM changes.", ["Persistence keeps access", "Privilege escalation expands capability", "Some techniques do both"], "Find unexpected scheduled tasks."),
    t("Defense evasion", "high", 55, "Disable detection, change logging, revert VMs, inject processes, or use bootkits.", ["Reduces visibility", "Logging changes are high signal", "Cloud events matter"], "Name logs revealing evasion."),
    t("Credential access and discovery", "high", 70, "Review brute force, password managers, keylogging, passwd/shadow, DCSync, tickets, and policy listing.", ["Credentials drive movement", "Discovery maps environment", "Clear-text secrets are common"], "Sketch a credential path."),
    t("Lateral movement and collection", "high", 65, "Use SSH, RDP, SMB, shared content, tokens, cookies, dumps, capture, and drives.", ["Movement crosses systems", "Collection gathers value", "Internal context changes detection"], "Map a lateral movement path."),
    t("Exfiltration, C2, impact", "high", 65, "Review USB, Bluetooth, DNS exfil, cloud storage, web C2, steganography, ransomware, defacement, and DoS.", ["Exfil removes data", "C2 maintains control", "Impact changes business operations"], "Map ransomware to attack stages.")
  ]),
  week(13, "Threat Modelling", "Architecture review, trust boundaries, frameworks, and risk.", [
    t("When to threat model", "medium", 40, "Use it for design, prioritization, hunting, detection, and risk assessments.", ["Earlier is cheaper", "Helps negotiate priorities", "Useful for detection development"], "Pick a feature and time the model."),
    t("Data flow diagrams", "medium", 45, "Create a system map with components, stores, flows, and boundaries.", ["Draw components", "Mark trust boundaries", "Use diagram to find threats"], "Draw a login DFD."),
    t("Trust boundaries", "medium", 45, "Identify where assumptions change.", ["User to service", "Service to database", "Cloud identity vs network trust"], "Mark boundaries on a simple app."),
    t("STRIDE", "high", 60, "Spoofing, tampering, repudiation, information disclosure, denial of service, elevation of privilege.", ["Authenticity", "Integrity", "Accountability", "Confidentiality", "Availability", "Authorization"], "Apply STRIDE to file upload."),
    t("DREAD", "medium", 35, "Damage, reproducibility, exploitability, affected users, discoverability and its limitations.", ["Subjective scoring", "Can take too much effort", "Useful as context"], "Explain why DREAD is often obsolete."),
    t("MITRE, PASTA, TRIKE, OCTAVE", "medium", 45, "Recognize common frameworks and when they help.", ["MITRE maps tactics and techniques", "PASTA is risk-centered", "Choose frameworks that support decisions"], "Compare STRIDE and MITRE usage.")
  ]),
  week(14, "Detection", "Signals, triage, signatures, logs, and tools.", [
    t("IDS and SIEM", "high", 55, "Understand Snort, Suricata, OSSEC, and SIEM correlation.", ["IDS can be signature or behavior based", "SIEM triages logs", "Alert fatigue matters"], "Compare Snort and Splunk."),
    t("IOCs", "medium", 35, "Use IPs, hashes, domains, and specific details as shared indicators.", ["Useful but narrow", "Can expire quickly", "Needs context"], "List IOC types for C2."),
    t("Signatures", "high", 60, "Detect registry changes, files, strings, malware samples, DNS, and C2 patterns.", ["Host signatures see endpoint changes", "Network signatures see traffic", "YARA can match files"], "Write a plain-language YARA detection."),
    t("Anomaly detection", "high", 55, "Detect deviations in URLs, login times, file access, commands, and /proc access.", ["Model normal behavior", "Tune false positives", "Increase logging for suspicious users"], "Describe one false positive."),
    t("Firewall and traffic detections", "medium", 45, "Watch brute force, port scans, half connections, antivirus notifications, and uploads.", ["SYNs without completion can indicate scanning", "Upload spikes may indicate exfil", "Slow attacks evade thresholds"], "Detect slow port scanning."),
    t("Honeypots and canary tokens", "medium", 40, "Use decoys to create high-signal alerts.", ["Dummy services reveal attackers", "Canary tokens alert on access", "Placement matters"], "Place three canaries."),
    t("Detection tools", "medium", 45, "Know Splunk, ArcSight, QRadar, Darktrace, tcpdump, Wireshark, and Zeek.", ["Log analytics", "Packet inspection", "Network metadata"], "Pick a tool for three tasks.")
  ]),
  week(15, "Digital Forensics", "Evidence across network, disk, memory, mobile, and custody.", [
    t("Evidence volatility", "medium", 35, "Prioritize network, memory, and disk based on lifetime.", ["Memory is volatile", "Network state changes quickly", "Collection order matters"], "Rank evidence sources."),
    t("Network forensics", "high", 50, "Use DNS logs, passive DNS, NetFlow, and sampling rate.", ["DNS reveals lookups", "NetFlow shows conversations", "Sampling affects completeness"], "Explain sampling risk."),
    t("Disk forensics", "high", 65, "Review imaging, filesystems, logs, recovery, carving, plaso, FTK Imager, and EnCase.", ["Image before analysis", "Know NTFS, ext, APFS", "Carving recovers by pattern"], "Create an imaging checklist."),
    t("Memory forensics", "very-high", 75, "Study acquisition, smear, hiberfiles, virtual vs physical memory, kernel/user space, Volatility, GRR, Rekall, and WinDbg.", ["Memory reveals runtime state", "Acquisition can alter evidence", "Tools answer different questions"], "Explain memory collection urgency."),
    t("Mobile forensics", "high", 50, "Compare Android, iPhone, jailbreaking, and mobile-specific evidence.", ["Different security models", "Jailbreaking affects access and integrity", "Cloud backups may matter"], "Compare iOS and Android evidence."),
    t("Anti-forensics", "high", 45, "Study hiding behavior and timestomping.", ["Attackers alter timestamps", "Correlate multiple sources", "Malware may hide processes or files"], "Reveal timestomping with timelines."),
    t("Chain of custody", "medium", 35, "Track evidence handoff and integrity.", ["Document handlers", "Hash evidence", "Keep work repeatable"], "Draft a custody entry.")
  ]),
  week(16, "Incident Management", "Run incidents from alert through lessons learned.", [
    t("Privacy vs security incidents", "medium", 35, "Classify incident type and escalation path.", ["Privacy and security can overlap", "Legal duties differ", "Communication changes"], "Classify three scenarios."),
    t("Stakeholder communication", "medium", 45, "Know when to involve legal, users, managers, and directors.", ["Manage expectations", "Choose channels carefully", "Tailor detail"], "Write a leadership update."),
    t("Roles and delegation", "medium", 45, "Assign investigation, communication, containment, and documentation.", ["Clear roles reduce duplicated effort", "Use playbooks", "Keep timeline"], "Define four incident roles."),
    t("Containment timing", "high", 55, "Stop attacks while managing the risk of alerting attackers.", ["Fast containment can lose visibility", "Delayed containment increases risk", "Evidence before blocking can matter"], "Explain a containment tradeoff."),
    t("Root cause and timeline", "high", 55, "Separate symptoms from causes and build event timelines.", ["Find initial path", "Connect attack stages", "Prevent recurrence"], "Build a timeline from five events."),
    t("PICERL and IMAG", "medium", 40, "Use response models to avoid missed steps.", ["Preparation", "Identification", "Containment", "Eradication", "Recovery", "Lessons learned"], "Map an incident to PICERL."),
    t("Assume good intent", "low", 30, "Work with people rather than against them during stressful incidents.", ["Blame slows learning", "Trust helps gather facts", "Postmortems should improve systems"], "Write three blameless action items.")
  ]),
  week(17, "Coding and Security Challenges", "Algorithms, Python fluency, and security-themed practice.", [
    t("Programming basics", "medium", 55, "Review conditions, loops, dictionaries, arrays, string operations, regex, and pseudocode.", ["Use pseudocode", "Know split/contains/length", "Write expected outputs"], "Pseudocode a log parser."),
    t("Data structures", "medium", 50, "Study dictionaries, arrays, stacks, SQL tables, and Bigtables.", ["Hash tables map keys to values", "Stacks are LIFO", "Tables structure relational data"], "Choose structures for deduplication."),
    t("Sorting and searching", "high", 60, "Review quicksort, merge sort, binary search, and linear search.", ["Binary search needs sorted input", "Know time and space Big O", "Compare sort tradeoffs"], "Explain binary search complexity."),
    t("Regex, recursion, Python", "high", 65, "Practice regex syntax, recursion limits, list comprehensions, generators, iterators, slicing, and dynamic types.", ["Regex can become expensive", "Recursion is not always practical", "Python fluency matters"], "Write a safe domain regex."),
    t("Cipher challenge", "medium", 60, "Implement a simple cipher or encoder.", ["Focus on text transformation", "Test round trips", "Explain limitations"], "Build a Caesar cipher with tests."),
    t("Log parser challenge", "high", 90, "Extract domains, executable names, timestamps, and indicators from logs.", ["Normalize timestamps", "Use structured output", "Test edge cases"], "Parse a sample access log."),
    t("Port scanner challenge", "high", 90, "Write a simple port scanner or scan detector for authorized local targets.", ["Handle timeouts", "Respect boundaries", "Summarize open ports"], "Scan localhost or detect scan patterns."),
    t("PDF metadata and malware signatures", "high", 90, "Build mini tools for metadata extraction or signature matching.", ["Inspect metadata", "Match strings in samples", "Publish work-in-progress scripts"], "Extract metadata or draft a YARA-like matcher.")
  ])
];

/* ============================================================
   DATA HELPERS  (hoisted — referenced by PLAN above)
   ============================================================ */
function week(number, section, summary, topics) {
  return {
    number, section, summary,
    topics: topics.map((item, index) => ({
      ...item,
      id: `w${number}-${slug(item.title)}`,
      week: number,
      section,
      index
    }))
  };
}
function t(title, difficulty, minutes, summary, details, practice) {
  return { title, difficulty, minutes, summary, details, practice };
}
function slug(v) {
  return v.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
function esc(v) {
  return String(v).replace(/[&<>"']/g, c => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c]
  ));
}

/* ============================================================
   STATE
   ============================================================ */
let state = loadState();

function loadState() {
  const blank = { version: 1, week: 1, selected: null, topics: {} };
  try { return { ...blank, ...(JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}) }; }
  catch { return blank; }
}
function saveState() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}
function topicState(topic) {
  if (!state.topics[topic.id]) {
    state.topics[topic.id] = {
      day: defaultDay(topic),
      done: false,
      completedAt: "",
      reviewCount: 0,
      nextReview: "",
      lastReviewed: "",
      notes: ""
    };
  }
  return state.topics[topic.id];
}

/* ============================================================
   PURE HELPERS
   ============================================================ */
function el(id)        { return document.getElementById(id); }
function allTopics()   { return PLAN.flatMap(w => w.topics); }
function currentWeek() { return PLAN.find(w => w.number === state.week) || PLAN[0]; }
function defaultDay(topic) { return DAYS[topic.index % DAYS.length]; }
function todayIso()    { const d = new Date(); d.setHours(0,0,0,0); return d.toISOString().slice(0,10); }
function todayName()   { return DAYS[(new Date().getDay() + 6) % 7]; }
function addDays(iso, n) {
  const d = new Date(`${iso}T00:00:00`);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0,10);
}
function pct(topics) {
  return topics.length
    ? Math.round(topics.filter(t => topicState(t).done).length / topics.length * 100)
    : 0;
}

function dueState(topic) {
  const s = topicState(topic);
  if (!s.done || !s.nextReview) return "none";
  if (s.nextReview < todayIso()) return "overdue";
  if (s.nextReview === todayIso()) return "due";
  return "scheduled";
}
function status(topic) {
  const d = dueState(topic);
  if (d === "overdue" || d === "due") return d;
  return topicState(topic).done ? "done" : "open";
}

function filteredTopics() {
  const query      = els.search.value.trim().toLowerCase();
  const wantStatus = els.statusFilter.value;
  const difficulty = els.difficultyFilter.value;
  const day        = els.dayFilter.value;
  return currentWeek().topics.filter(topic => {
    const s    = topicState(topic);
    const text = [topic.title, topic.summary, topic.section, ...topic.details, topic.practice]
                   .join(" ").toLowerCase();
    if (query && !text.includes(query)) return false;
    if (difficulty !== "all" && topic.difficulty !== difficulty) return false;
    if (day !== "all" && s.day !== day) return false;
    if (wantStatus === "open"    &&  s.done)                     return false;
    if (wantStatus === "done"    && !s.done)                     return false;
    if (wantStatus === "due"     && dueState(topic) !== "due")     return false;
    if (wantStatus === "overdue" && dueState(topic) !== "overdue") return false;
    return true;
  });
}

/* ============================================================
   CHIP HELPERS
   ============================================================ */
function difficultyChip(topic) {
  const labels = { low: "Low", medium: "Medium", high: "High", "very-high": "Very High" };
  return `<span class="chip ${topic.difficulty}">${labels[topic.difficulty] || topic.difficulty}</span>`;
}
function statusChip(topic) {
  const st = status(topic);
  if (st === "overdue") return `<span class="chip overdue-chip">Overdue</span>`;
  if (st === "due")     return `<span class="chip due-chip">Due today</span>`;
  if (st === "done")    return `<span class="chip done-chip">Done</span>`;
  return `<span class="chip">To learn</span>`;
}

/* ============================================================
   RENDER
   ============================================================ */
let els;

function render() {
  const wt = currentWeek().topics;
  if (!wt.some(t => t.id === state.selected)) state.selected = wt[0]?.id || null;
  renderWeeks();
  renderStats();
  renderGrid();
  renderList();
  renderToday();
  renderDetail();
  saveState();
}

function renderWeeks() {
  els.weekList.innerHTML = PLAN.map(item => {
    const done     = item.topics.filter(t => topicState(t).done).length;
    const isActive = item.number === state.week;
    return `<button class="week-btn${isActive ? " active" : ""}" data-week="${item.number}" type="button">
      <span class="week-num">${item.number}</span>
      <span>
        <span class="week-name">${esc(item.section)}</span>
        <span class="week-sub">${done}/${item.topics.length} complete</span>
      </span>
    </button>`;
  }).join("");

  els.weekList.querySelectorAll(".week-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      state.week     = Number(btn.dataset.week);
      state.selected = null;
      render();
    });
  });
}

function renderStats() {
  const all        = allTopics();
  const weekTopics = currentWeek().topics;
  const done       = all.filter(t => topicState(t).done).length;
  const reviews    = all.filter(t => ["due", "overdue"].includes(dueState(t)));
  const todayOpen  = weekTopics.filter(t => topicState(t).day === todayName() && !topicState(t).done);

  els.weekTitle.textContent    = `Week ${currentWeek().number}: ${currentWeek().section}`;
  els.weekMeta.textContent     = `${weekTopics.length} topics`;
  els.weekSummary.textContent  = currentWeek().summary;
  els.globalPercent.textContent = `${pct(all)}%`;
  els.globalBar.style.width    = `${pct(all)}%`;
  els.completedCount.textContent = `${done}/${all.length}`;
  els.weekBar.style.width      = `${pct(weekTopics)}%`;
  els.reviewCount.textContent  = reviews.length;
  els.reviewHint.textContent   = reviews.length
    ? `${reviews.length} review${reviews.length === 1 ? "" : "s"} need attention.`
    : "Nothing due.";
  els.todayCount.textContent   = todayOpen.length;
  els.todayHint.textContent    = todayOpen.length
    ? `${todayOpen.length} topic${todayOpen.length === 1 ? "" : "s"} assigned.`
    : "No topics assigned.";
  els.todayDate.textContent    = todayIso();
  els.visibleCount.textContent = `${filteredTopics().length} visible`;
}

function renderGrid() {
  const visible = filteredTopics();
  els.grid.innerHTML = DAYS.concat("Unscheduled").map(day => {
    const items   = visible.filter(t => topicState(t).day === day);
    const isToday = day === todayName();
    return `<div class="day-col${isToday ? " is-today" : ""}">
      <div class="day-head">
        <span>${day}</span>
        <span class="day-count">${items.length}</span>
      </div>
      <div class="day-body">
        ${items.length
          ? items.map(cardHtml).join("")
          : `<div class="empty-state">No topics</div>`}
      </div>
    </div>`;
  }).join("");
  bindCardControls(els.grid);
}

function cardHtml(topic) {
  const s         = topicState(topic);
  const st        = status(topic);
  const isSelected = state.selected === topic.id;
  const dayOpts   = DAYS.concat("Unscheduled")
    .map(d => `<option${s.day === d ? " selected" : ""}>${d}</option>`)
    .join("");
  return `<div class="topic-card ${st}${isSelected ? " selected" : ""}" data-topic="${topic.id}">
    <div class="card-title">
      <input type="checkbox" data-action="done"${s.done ? " checked" : ""} title="Mark complete">
      <span>${esc(topic.title)}</span>
    </div>
    <div class="chips">${difficultyChip(topic)}${statusChip(topic)}<span class="chip">${topic.minutes} min</span></div>
    <select class="day-select" data-action="day" aria-label="Schedule ${esc(topic.title)}">${dayOpts}</select>
  </div>`;
}

function renderList() {
  const visible = filteredTopics();
  els.topicList.innerHTML = visible.length
    ? visible.map(topic => {
        const s          = topicState(topic);
        const st         = status(topic);
        const isSelected = state.selected === topic.id;
        return `<div class="topic-row ${st}${isSelected ? " selected" : ""}" data-topic="${topic.id}">
          <h3>${esc(topic.title)}</h3>
          <p>${esc(topic.summary)}</p>
          <div class="chips">${difficultyChip(topic)}${statusChip(topic)}<span class="chip">${s.day}</span></div>
        </div>`;
      }).join("")
    : `<div class="empty-state" style="padding:20px">No topics match the current filters.</div>`;

  els.topicList.querySelectorAll("[data-topic]").forEach(row => {
    row.addEventListener("click", () => { state.selected = row.dataset.topic; render(); });
  });
}

function renderToday() {
  const due = allTopics().filter(t => ["due", "overdue"].includes(dueState(t)));
  const sched = currentWeek().topics.filter(t => topicState(t).day === todayName() && !topicState(t).done);
  // deduplicate (a due topic could also be scheduled today)
  const seen = new Set();
  const queue = [...due, ...sched].filter(t => !seen.has(t.id) && seen.add(t.id)).slice(0, 10);

  els.todayQueue.innerHTML = queue.length
    ? queue.map(topic =>
        `<li class="queue-item" data-topic="${topic.id}" data-week="${topic.week}">
          <strong>${esc(topic.title)}</strong>
          <div class="chips"><span class="chip">Week ${topic.week}</span>${statusChip(topic)}</div>
        </li>`
      ).join("")
    : `<li class="empty-state">Nothing due today. Pull one hard topic forward if you have time.</li>`;

  els.todayQueue.querySelectorAll("[data-topic]").forEach(item => {
    item.addEventListener("click", () => {
      state.week     = Number(item.dataset.week);
      state.selected = item.dataset.topic;
      render();
    });
  });
}

function renderDetail() {
  const topic = allTopics().find(t => t.id === state.selected) || currentWeek().topics[0];
  if (!topic) {
    els.detail.innerHTML = `<p style="color:var(--text-3);font-size:13px">Select a topic to view details.</p>`;
    return;
  }
  const s      = topicState(topic);
  const dayOpts = DAYS.concat("Unscheduled")
    .map(d => `<option${s.day === d ? " selected" : ""}>${d}</option>`)
    .join("");

  els.detail.innerHTML = `
    <p class="detail-summary">${esc(topic.summary)}</p>
    <div class="chips">${difficultyChip(topic)}${statusChip(topic)}<span class="chip">Week ${topic.week}</span><span class="chip">${topic.minutes} min</span></div>
    <div class="detail-actions">
      <button class="btn-primary" data-detail="toggle" type="button">${s.done ? "Mark not done" : "Mark complete"}</button>
      <button data-detail="review" type="button"${s.done ? "" : " disabled"}>Mark reviewed</button>
      <button data-detail="defer" type="button">Defer one day</button>
      <select data-detail="day" aria-label="Move selected topic">${dayOpts}</select>
    </div>
    <p class="detail-meta">Completed: ${s.completedAt || "Not yet"}<br>Reviews: ${s.reviewCount}<br>Next review: ${s.nextReview || "Not scheduled"}</p>
    <h3>Study points</h3>
    <ul class="study-list">${topic.details.map(d => `<li>${esc(d)}</li>`).join("")}</ul>
    <h3>Practice</h3>
    <div class="practice-box">${esc(topic.practice)}</div>
    <h3>Personal notes</h3>
    <textarea id="notesArea" placeholder="Add examples, questions, commands, links, or weak spots."></textarea>
    <p class="hint" id="noteStatus">Saved locally in this browser.</p>`;

  // set textarea value via JS to avoid HTML-entity issues
  els.detail.querySelector("#notesArea").value = s.notes;

  els.detail.querySelector('[data-detail="toggle"]').addEventListener("click",  () => toggleDone(topic, !s.done));
  els.detail.querySelector('[data-detail="review"]').addEventListener("click",  () => markReviewed(topic));
  els.detail.querySelector('[data-detail="defer"]').addEventListener("click",   () => defer(topic));
  els.detail.querySelector('[data-detail="day"]').addEventListener("change",    e  => { s.day = e.target.value; render(); });
  els.detail.querySelector("#notesArea").addEventListener("input", e => {
    s.notes = e.target.value;
    saveState();
    el("noteStatus").textContent = "Saved.";
  });
}

function bindCardControls(root) {
  root.querySelectorAll(".topic-card").forEach(card => {
    const topic = allTopics().find(t => t.id === card.dataset.topic);
    if (!topic) return;
    card.addEventListener("click", e => {
      if (e.target.matches("input[type='checkbox'], select, option")) return;
      state.selected = topic.id;
      render();
    });
    card.querySelector('[data-action="done"]').addEventListener("change", e =>
      toggleDone(topic, e.target.checked)
    );
    card.querySelector('[data-action="day"]').addEventListener("change", e => {
      topicState(topic).day = e.target.value;
      render();
    });
  });
}

/* ============================================================
   TOPIC ACTIONS
   ============================================================ */
function toggleDone(topic, done) {
  const s = topicState(topic);
  s.done = done;
  if (done) {
    s.completedAt  = todayIso();
    s.reviewCount  = 0;
    s.lastReviewed = "";
    s.nextReview   = addDays(todayIso(), REVIEW_INTERVALS[0]);
  } else {
    s.completedAt  = "";
    s.reviewCount  = 0;
    s.lastReviewed = "";
    s.nextReview   = "";
  }
  render();
}

function markReviewed(topic) {
  const s = topicState(topic);
  if (!s.done) return;
  s.lastReviewed = todayIso();
  s.reviewCount += 1;
  s.nextReview   = addDays(todayIso(), REVIEW_INTERVALS[Math.min(s.reviewCount, REVIEW_INTERVALS.length - 1)]);
  render();
}

function defer(topic) {
  const s = topicState(topic);
  const i = DAYS.indexOf(s.day);
  s.day = i === -1 ? "Monday" : DAYS[(i + 1) % DAYS.length];
  render();
}

/* ============================================================
   INIT
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  els = {
    weekList:       el("weekList"),
    weekTitle:      el("weekTitle"),
    weekMeta:       el("weekMeta"),
    weekSummary:    el("weekSummary"),
    search:         el("search"),
    statusFilter:   el("statusFilter"),
    difficultyFilter: el("difficultyFilter"),
    dayFilter:      el("dayFilter"),
    grid:           el("grid"),
    topicList:      el("topicList"),
    visibleCount:   el("visibleCount"),
    detail:         el("detail"),
    todayQueue:     el("todayQueue"),
    todayDate:      el("todayDate"),
    globalPercent:  el("globalPercent"),
    globalBar:      el("globalBar"),
    completedCount: el("completedCount"),
    weekBar:        el("weekBar"),
    reviewCount:    el("reviewCount"),
    reviewHint:     el("reviewHint"),
    todayCount:     el("todayCount"),
    todayHint:      el("todayHint"),
    autoFill:       el("autoFill"),
    clearFilters:   el("clearFilters"),
    resetWeek:      el("resetWeek"),
    resetAll:       el("resetAll"),
    exportState:    el("exportState"),
    importState:    el("importState"),
    backupText:     el("backupText"),
    backupStatus:   el("backupStatus")
  };

  [els.search, els.statusFilter, els.difficultyFilter, els.dayFilter]
    .forEach(c => c.addEventListener("input", render));

  els.autoFill.addEventListener("click", () => {
    currentWeek().topics.forEach((topic, i) => {
      if (!topicState(topic).done) topicState(topic).day = DAYS[i % DAYS.length];
    });
    render();
  });

  els.clearFilters.addEventListener("click", () => {
    els.search.value             = "";
    els.statusFilter.value       = "all";
    els.difficultyFilter.value   = "all";
    els.dayFilter.value          = "all";
    render();
  });

  els.resetWeek.addEventListener("click", () => {
    if (!confirm(`Reset Week ${currentWeek().number} progress and notes?`)) return;
    currentWeek().topics.forEach(t => delete state.topics[t.id]);
    state.selected = null;
    render();
  });

  els.resetAll.addEventListener("click", () => {
    if (!confirm("Reset all progress, reviews, notes, and scheduling?")) return;
    state = { version: 1, week: 1, selected: null, topics: {} };
    render();
  });

  els.exportState.addEventListener("click", () => {
    els.backupText.value       = JSON.stringify(state, null, 2);
    els.backupStatus.textContent = "Backup exported into the text box.";
  });

  els.importState.addEventListener("click", () => {
    try {
      const imported = JSON.parse(els.backupText.value);
      if (!imported || !imported.topics) throw new Error("Invalid state");
      state = { version: 1, week: 1, selected: null, topics: {}, ...imported };
      els.backupStatus.textContent = "Backup imported.";
      render();
    } catch {
      els.backupStatus.textContent = "Import failed. Paste valid planner backup JSON.";
    }
  });

  render();
});
