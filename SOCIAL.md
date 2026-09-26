# We built a tool to grade Sri Lanka's government websites 🇱🇰

At the Lanka Data Foundation's citizen-led Government Website Scorecard
Hackathon on September 5th, a few of us started **Grading Government
Websites (`glwa`)**. It was a sub-project to automate checks that software could
run reliably.

`glwa` grades sites from Level 0, where a site does not work, to Level 5, where
public services are connected and proactive. Levels 0-3 are implemented so
far.

It audits the government web directory, saves the evidence, and marks checks as
pass, fail, or inconclusive. Each site gets a report, plus JSON and CSV data.

The dashboard 📊 lets you search and sort results, browse by ministry, and open
the evidence behind each grade. It uses saved reports, so browsing it makes no
live requests to government websites.

One important caveat: the hackathon was much bigger. Participants also looked
at things that need human judgement. `glwa` covers the automatable slice, not
the full hackathon scorecard (See Report below).

Built by Ranuga Disansa, Dushmilan Jeyanathan, Malin Ruwanpathirana and Nuwan Senaratna.

A big thank you 🙌 to Zaeema Nashath of the #LDF who helped us.

This is still very much a work in progress 🛠️, so ideas and contributions are
welcome. Feel free to fork the repo and build on it too.

REPO: <https://github.com/nuuuwan/gov_lk_web_auditor>
DASHBOARD: <https://nuuuwan.github.io/gov_lk_web_auditor>
LDF HACKATHON: <https://www.linkedin.com/posts/lankadata_ldf-government-website-scorecard-ugcPost-7509307084316827649-iZGF>
LDF AUDIT REPORT: <https://drive.google.com/file/d/1HnHyltlOsA7Wvh9BIB1VN6s07yQTcxEH/view>

# SriLanka #CivicTech #DigitalGovernment #OpenSource
