export interface TeamGuideEntry {
  name: string
  description: string
}

export const TEAM_GUIDE: TeamGuideEntry[] = [
  {
    name: '(BF) Employee Platform (SAP SF)',
    description:
      'This team supports the employee platform, also known as SAP SuccessFactors. SuccessFactors is a human-resources system used to manage employee information and HR processes. Typical areas include Employee Central, recruitment, learning and training, time off, attendance, work schedules, and employee qualification information. Tickets from local HR users about changing or correcting employee data generally belong here.',
  },
  {
    name: '(BF) Information Security Office',
    description:
      'This team handles security governance for privileged access to computers and systems. Administrator rights are permissions that allow a user to install software or change protected computer settings. Requests to receive, renew, or approve administrator access belong here when the central subject is elevated privilege, even if the user also mentions a particular program or computer.',
  },
  {
    name: '(GI-CyberSec) Security Operation Center',
    description:
      'The Security Operation Center, or SOC, monitors and investigates security-related events. It deals with suspicious messages, quarantined email, blocked or potentially dangerous attachments, malware or virus warnings, and requests to trust a sender or domain. In general, this is the team for deciding whether content or activity is safe, rather than for ordinary computer maintenance.',
  },
  {
    name: '(GI-IaaS) Admin - License & Asset Management',
    description:
      'This team manages software and hardware-related administration. Its work includes installing or licensing software, supplying software such as Visual Studio or Docker, managing device plans, and making directory-group changes. A directory group is a centrally managed list of users used to grant access to systems. The team is concerned with the administrative lifecycle of software, licenses, and assets.',
  },
  {
    name: '(GI-IaaS) Azure Data Center',
    description:
      "This team supports infrastructure hosted in the Azure data-center environment. Azure is Microsoft's cloud platform, where organizations run virtual machines, applications, storage, and other computing resources. Tickets about Azure subscriptions or infrastructure resources belong here when they concern the data-center layer itself. Here can also be SAP or Synertrade issues associated with this infrastructure area.",
  },
  {
    name: '(GI-IaaS) Backend Application Srv. & Project Support',
    description:
      'This team supports backend servers and the technical platforms on which applications run. A backend server provides processing or storage for applications rather than being the user\'s personal computer. The team commonly handles virtual machines, server access, application-server support, virtual-device retirement during offboarding, Owncloud storage, and migrations involving platforms such as Confluence.',
  },
  {
    name: '(GI-IaaS) Cloud Services',
    description:
      'This team administers cloud accounts and cloud subscriptions. The observed platforms include Google Cloud, Microsoft Azure, and AWS. A cloud account or project is an online environment where an organization manages computing resources, users, and permissions. Requests to create a Google account, add a user to a cloud project, manage Azure subscription membership, or renew a cloud subscription generally belong here.',
  },
  {
    name: '(GI-IaaS) Development Platform',
    description:
      'This team owns tools used by software-development and project teams to plan, build, and document work. Jira and Jira Service Management track work and service requests; Confluence stores shared documentation; Azure DevOps supports development workflows; Git stores source code; and Miro provides collaborative visual boards. Licenses, projects, permissions, configuration, and access problems for these developer tools belong here.',
  },
  {
    name: '(GI-IaaS) Network Cloud (Azure, Remote Access)',
    description:
      'This team supports network connectivity at the cloud and remote-access layer. It is concerned with how remote users, servers, cloud resources, and services reach one another through a network. Typical subjects include access from a VPN-connected environment to a server or business destination, remote-access service availability, VPN-node problems, and Azure network connectivity. The emphasis is on the shared remote or cloud infrastructure rather than a single user\'s computer.',
  },
  {
    name: '(GI-IaaS) Network On-Prem (LAN,WLAN,WAN 2nd level)',
    description:
      'This team supports internal physical and enterprise network infrastructure. LAN means a local area network, WLAN means a wireless local area network, and WAN means a wide area network connecting locations. The team handles higher-level network changes and incidents such as site-to-site tunnels with partners, network endpoints, switches, and other on-premises connectivity. A site-to-site tunnel is a persistent secured connection between two organizations or network locations.',
  },
  {
    name: '(GI-SM) Service Desk',
    description:
      'This team provides broad service administration and first-level coordination for requests that do not clearly belong to a specialist team. It supports the service-management system itself, including iTop and CMDB data. A CMDB, or configuration management database, records devices, applications, services, and their relationships. The team also appears in general requests involving service records, contracts, bulk data updates, and miscellaneous tool support.',
  },
  {
    name: '(GI-SaaS) SAP & Synertrade',
    description:
      'This team supports business applications used for purchasing, finance, and related enterprise processes. SAP is a broad enterprise resource-planning platform, while Synertrade is used for purchasing and supplier processes. Typical subjects include suppliers, purchase orders, invoices, approval flows, SAP users, and information transferred between SAP and Synertrade. Choose this team when the ticket is about the behavior or data of those business applications.',
  },
  {
    name: '(GI-SaaS) Salesforce',
    description:
      'This team supports Salesforce-related business applications, especially Kimble. Kimble is a business system used for professional-services work such as time recording, absences, engagements, sales opportunities, permissions, and project-related data. This team generally handles business-process access and data changes, such as correcting an absence, changing permissions, or updating an engagement.',
  },
  {
    name: '(GI-UX) Account Management',
    description:
      "This team manages user accounts and the lifecycle of people joining, changing roles, or leaving the organization. Onboarding means preparing accounts, permissions, equipment, and services for a new employee or contractor. Offboarding means removing or disabling those resources when someone leaves. The team also handles collaboration invitations, email distribution groups, and other account-level changes associated with a person's employment lifecycle.",
  },
  {
    name: '(GI-UX) Application',
    description:
      'This team handles end-user application problems, with the observed examples focused on Kimble. The emphasis is on a technical failure or unexpected behavior in the application rather than a business permission or data-change request. Examples include a timesheet that cannot be submitted, an absence workflow stuck in the wrong state, or an application calculation that does not behave as expected. The team represents application-level support from the user\'s perspective.',
  },
  {
    name: '(GI-UX) File & Print',
    description:
      'This team supports everyday workplace equipment and local end-user services. It covers computers, monitors, keyboards, mice, printers, local software problems, and the assignment or retirement of devices. It also appears in a small number of file-storage and source-control related requests when they are treated as end-user support. Think of this team as responsible for the practical workstation and peripheral experience.',
  },
  {
    name: '(GI-UX) Group',
    description:
      'This is a broad end-user support team for common workplace requests that do not have a clearer specialist owner. Observed subjects include password resets, ordinary PC problems, general software help, and broad requests involving endpoint, email, network, or group access. The label is most appropriate when the ticket describes a routine user-support need without enough detail to identify a specialist service.',
  },
  {
    name: '(GI-UX) Mobile Device Management',
    description:
      'This team manages company mobile phones and mobile-device enrollment. Mobile Device Management, or MDM, is the system used to configure, secure, and control company smartphones and tablets. The team handles new phones, replacements, accessories, mobile-device problems, phone enrollment, and authentication-app registration. Use it for the mobile device itself rather than for a general user account or desktop computer.',
  },
  {
    name: '(GI-UX) Network Access',
    description:
      'This team supports network access from an individual user\'s computer. Common subjects include installing or using a VPN client, a VPN connection that fails, and a user who cannot reach a destination while connected to the company network. A VPN, or virtual private network, creates an encrypted connection from a device to a company or partner network. This team is focused on the end-user connection experience.',
  },
  {
    name: '(GI-UX) Office365 & MS-Teams',
    description:
      'This team supports Microsoft\'s everyday collaboration services. Microsoft 365 includes cloud versions of tools such as OneDrive, while Microsoft Teams provides chat, meetings, calls, teams, and channels. The team handles OneDrive synchronization and sharing, Teams problems, new teams or channels, Teams calling, and general collaboration-tool usage. It is about using and administering workplace collaboration services rather than developing software.',
  },
  {
    name: '(GI-UX) System Management & Anti Virus',
    description:
      'This team manages endpoint configuration and protection on user devices. Endpoint management means centrally controlling computer settings, policies, updates, and security tools. Observed subjects include Configuration Manager, device policies, protected Windows settings, hosts-file changes, and local antivirus behavior. Use this team for routine endpoint security or configuration management, while security investigations involving suspicious mail or content belong to the Security Operation Center.',
  },
  {
    name: '(GI-UX) Unified Communication',
    description:
      'This team supports email and Outlook-based communication. Unified communication refers to connected communication services such as email, calendars, aliases, and distribution groups. Typical tickets concern mailbox or Outlook problems, calendar behavior, email aliases, and membership or usage of email distribution groups. The team is focused on communication services rather than broader Microsoft Teams collaboration.',
  },
  {
    name: '(GI-UX) Windows',
    description:
      'This team supports the Windows operating system and Windows-specific behavior on workplace computers. It handles local Windows software problems, operating-system warnings, updates, and Windows-specific configuration issues. It may also appear when a VPN or Citrix problem is clearly caused by the Windows workstation. Choose it when the operating system is the central subject, rather than when the request is primarily for a license, privileged access, or generic hardware support.',
  },
  {
    name: '(LF) IT Office Access Italy',
    description:
      'This team manages physical access to GFT offices in Italy. Physical access includes building badges, office permissions, access to additional locations, and problems entering a building. It also handles lost cards and removal of office access during offboarding. These tickets concern access to a physical location, not access to an application, account, or computer.',
  },
]

export const TEAM_GUIDE_BY_NAME = Object.fromEntries(
  TEAM_GUIDE.map((entry) => [entry.name, entry]),
) as Record<string, TeamGuideEntry>
