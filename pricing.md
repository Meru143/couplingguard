# Pricing — couplingguard

## Free

- **Price:** $0 forever
- **License:** MIT
- **Hosted service:** None — runs in your CI on your runner
- **Signup required:** None
- **Account required:** None (beyond a GitHub/GitLab account, which you already have)
- **Public repo cost:** $0 (GitHub Actions minutes are free for public repos)
- **Private repo cost:** $0 from couplingguard's side. GitHub Actions minutes are billed by GitHub at their standard rate (2,000 free minutes/month for Free plans, more for Pro/Team/Enterprise). A typical couplingguard run uses ~20-40 seconds of runner time per PR.

## No paid tier

couplingguard does not have a Pro plan, Team plan, Enterprise plan, or hosted version. There's no upsell. All features — `fail_threshold`, dashboard generation, GitLab CI support, CODEOWNERS reviewer suggestions — are available in the free MIT-licensed Action.

## How couplingguard makes money

It doesn't. couplingguard is open source software released under the MIT license by Meru143. No commercial offering, no hosted SaaS, no premium add-on. Maintenance is volunteer-driven; contributions welcome via the [GitHub repo](https://github.com/Meru143/couplingguard).

## Comparable commercial tools

For context if you're evaluating couplingguard against paid alternatives:

| Tool | Pricing model |
|---|---|
| **couplingguard** | Free, MIT |
| [CodeScene](https://codescene.com/) | Commercial, per-seat license |
| [Code Climate Quality](https://codeclimate.com/) | Paid tiers from ~$20/seat/month |
| [SonarQube](https://www.sonarsource.com/products/sonarqube/) | Free community edition; paid Server/Enterprise tiers |
| [code-maat](https://github.com/adamtornhill/code-maat) | Free (GPLv3), but CLI-only, no PR integration |

## Support

Free. Community-supported via:

- **Bug reports:** https://github.com/Meru143/couplingguard/issues
- **Feature requests:** https://github.com/Meru143/couplingguard/issues
- **Security disclosure:** see [SECURITY.md](SECURITY.md)
- **Source code:** https://github.com/Meru143/couplingguard

No SLAs. No commercial support contracts. No managed service.
