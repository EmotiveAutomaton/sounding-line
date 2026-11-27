# PSD2 · everyday-emotions checklist

The curator approved two descriptive same-prompt comparisons for internal tests only on November 25. Use the Trampe, Quoidbach and Taquet release retained from OSF project h2jp3. The pinned file SHA-256 is `05551223671df4b34f4c20ab197a61307e7922f46cc7f3c9feb0a302d362e02b`. The archive records no stated licence. Retain scientific figures only in the restricted return.

Project only the person key, pride, embarrassment (source spelling `Embarassment`) and guilt. Treat 1 as checked and 0 as unchecked. Exclude missing item responses pairwise. Reject unknown codes or absent person keys. For each pair include only people who endorsed each item at least once among complete prompts. Reuse PSD2’s joint_terms routine with a one-step threshold. Within person the joint endorsement fraction is divided by the product of that person's two marginal fractions. Average the ratios weighted by the number of complete prompts per eligible person. Return both pair-specific exclusions and 95% percentile intervals from 2,000 whole-person draws per pair, seed 20261125. A ratio of one corresponds to the person's marginal-independence expectation. Below 20 eligible people file support only.

## Design check

Method lessons §§2–5. Independent planted endorsements give one, synchronized half-frequency endorsements give two and disjoint endorsements give zero. Unequal prompt counts exercise the weighting rule. Missing responses, absent endorsements, invalid codes and the support boundary are checked on constructed inputs. No outcome is used for source qualification. A fresh native process must reproduce the return. The registered shame measure, intensity threshold and channel verdict remain open. The two descriptive comparisons concern distinct checklist words.

