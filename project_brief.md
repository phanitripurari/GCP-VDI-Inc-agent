# My agent: vdi-incident-agent
One-liner: A conversational agentic solution that helps VDI Engineers and Incident Responders troubleshoot and perform Root Cause Analysis (RCA) on VDI failures across Citrix, AVD, Horizon, and Windows 365.

Tool coverage:
- Memory: Session history and recurring incident context
- Tools: Diagnostic lookup and error code analysis
- Catalog/UI: n/a
- Image gen: n/a
- Sandbox: n/a

Core rails (everyone): memory, tools, eval, deploy, frontend
My stretch menu (pick later): A2UI, Firestore
First eval question: FSLogix profile attach failed with Error 0x80070035 on session host sh-avd-01. VHDX path \\storage\profiles\user1.vhdx is inaccessible.
