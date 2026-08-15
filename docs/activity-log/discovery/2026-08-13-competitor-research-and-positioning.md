# Competitor Research and Product Positioning

**Date:** August 13, 2026  
**Phase:** Discovery

## Goal

I want to build something that helps my teammates and coach understand what is happening across our matches without requiring them to review every point manually. My goal for this research was to determine whether existing products already solve that problem, identify where my idea overlaps with them, and define a more useful focus to test with my team and coach.

## What I did

I reviewed the official product information for several tennis video-analysis and coaching products:

- [SwingVision](https://swing.vision/home/)
- [Wingfield](https://help.wingfield.io/en/match-mode)
- [PlaySight SmartCourt](https://my.playsight.com/Home/WhatIsPlaySight)
- [Baseline Vision](https://www.baselinevision.com/)
- [OnCourtAI](https://www.oncourtai.co.uk/)
- [ProCourt](https://www.procourt.app/)

I compared their target users, equipment requirements, and features with what I want Ace Pro to do for my teammates and coach.

## Competitor findings

### SwingVision

SwingVision is the closest direct competitor. It uses an iPhone or iPad to record or import footage and offers automated scoring, shot statistics, placement, speed, rally length, line-call challenges, dead-time removal, highlights, heatmaps, and progress tracking.

This overlaps substantially with the initial Ace Pro concept of turning match video into statistics and searchable clips. Uploading existing footage is also not a unique differentiator because SwingVision already supports it.

What I have not yet confirmed is whether SwingVision helps a team move from individual statistics to a shared understanding of which recurring patterns matter most, why they matter, and what the coach should prioritize in practice. This is a question I need to test directly rather than assume.

### Wingfield

Wingfield provides match recording, serve and rally statistics, winners and errors, shot placement, speed, net clearance, highlights, and AI-assisted video navigation. It is more closely connected to equipped courts and clubs.

Wingfield may be less suitable for my immediate situation if using it depends on access to an equipped Wingfield court. I also need to test whether its reports support the team-and-coach decision workflow I have in mind or mainly provide analysis to individual players.

### PlaySight SmartCourt

PlaySight uses an installed multi-camera system to provide line calling, livestreaming, replay, automatic tagging, and detailed shot statistics. Its primary market appears to be clubs, academies, teams, and other facilities.

This could work well for a facility that already has the system, but it does not appear to solve the accessibility problem for teammates recording ordinary matches on devices they already own.

### Baseline Vision

Baseline Vision uses a portable dual-camera device mounted on a net post. It provides live statistics, line calling, replay, drills, and highlights. Its dedicated hardware makes it a different cost and setup category from a software-first product using existing footage.

The dedicated device may provide stronger tracking, but requiring specialized hardware could make it harder to analyze every teammate's matches consistently.

### Technique-analysis products

OnCourtAI and ProCourt focus more on individual stroke mechanics and coaching feedback from short clips. They compete with a possible future AI-coaching direction but less directly with full-match pattern analysis.

These products do not appear focused on discovering patterns across a complete competitive match or helping a coach compare evidence across several teammates.

## Why these products may not solve my specific problem

The competitors clearly solve important parts of tennis video analysis, and I cannot claim that Ace Pro is better without testing them. However, my proposed problem is narrower than generating statistics, highlights, or technique scores.

I want to help my teammates and coach:

- Find recurring patterns across a full match, not only isolated shots.
- Understand which findings are important enough to discuss or practice.
- Open the exact points that support each finding.
- Correct questionable AI detections instead of silently trusting them.
- Compare findings across players and matches.
- Turn match evidence into team and individual practice priorities.
- Use footage recorded with devices we already have whenever technically possible.

Based on the available product information, it is not yet clear that any one competitor provides this complete workflow. Direct testing is required to determine whether this is a real gap.

## Key findings

- The market validates that players and coaches are interested in video-based tennis analysis.
- The broad concept of match video becoming statistics and clips already exists.
- SwingVision covers most of the original feature-level concept and is the product Ace Pro must compare against directly.
- Statistics, searchable video, uploaded footage, and progress tracking are not sufficient differentiators by themselves.
- Hardware-based competitors leave some room for software that works with ordinary user-owned cameras, but SwingVision also provides a portable single-device experience.
- Ace Pro needs to solve a narrower user problem better instead of trying to reproduce a general tennis analytics platform.

## Proposed focus

I propose focusing Ace Pro on turning our match data into prioritized, evidence-backed decisions for my teammates and coach.

After a match, it should help answer:

1. What pattern happened repeatedly?
2. Where is the video evidence?
3. What deserves attention next?

Instead of only reporting a statistic such as:

> Backhand return percentage: 36%.

I want Ace Pro to produce an insight such as:

> You lost 64% of points when your backhand return landed short. Here are the seven relevant clips. This is the highest-priority pattern to review with the coach before the next practice.

## Proposed value proposition

> Upload our tennis matches. Discover the patterns affecting our performance. Give players and coaches the evidence needed to decide what to work on next.

A longer version is:

> Ace Pro turns ordinary tennis match video into prioritized, evidence-backed insights that help my teammates and coach understand what is affecting performance and decide what to work on next.

The intended positioning is not simply "more statistics." It is a progression from observations to decisions:

**Match video → detected events → recurring patterns → supporting clips → next priority**

## Proposed differentiators

These are proposed directions, not validated advantages:

- **Prioritized patterns:** Rank the findings that appear most important instead of presenting a large dashboard of equally weighted statistics.
- **Evidence for every insight:** Link each conclusion to the points and clips that support it.
- **Action-oriented interpretation:** Explain what changed during the match and what should be reviewed or tested next.
- **Transparent confidence:** Show when a detection or conclusion is uncertain.
- **Human correction:** Let players or coaches correct events and immediately update the analysis.
- **Coach collaboration:** Make it easy to review findings, add context, and turn them into practice priorities.
- **Ordinary footage:** Explore support for common phone, Android, GoPro, and uploaded recordings without requiring dedicated court hardware.

## Product hypotheses

### H8: Prioritized insights are more valuable than a large statistics dashboard

Players and coaches will get more value from a small number of ranked match patterns than from many unprioritized metrics.

**How to test:** Show interview participants an example statistics dashboard and an example prioritized insight report. Ask which one would affect their next practice or match preparation and why.

### H9: Video evidence increases trust and usefulness

Users will trust and act on an insight more often when they can immediately review every point supporting it.

**How to test:** Present the same finding with and without linked clips. Observe whether participants believe it, understand it, and can decide what to do next.

### H10: Correction is preferable to hidden uncertainty

Players and coaches will accept imperfect AI if uncertain events are clearly identified and can be corrected quickly.

**How to test:** Give participants a sample analysis containing uncertain and incorrect events. Measure whether they understand the confidence indicators and how much correction time they tolerate.

### H11: Match patterns can change practice decisions

Evidence-backed recurring patterns will help a player or coach select a more specific practice priority.

**How to test:** Ask coaches to review a sample match analysis and state what they would practice before and after seeing it.

### H12: Existing tools leave an interpretation gap

Some users of existing tennis analytics products receive statistics and video but still have difficulty deciding which findings matter and what action to take.

**How to test:** Interview current or former SwingVision users about which outputs they use, which they ignore, what they distrust, and whether the analysis changes their training.

### H13: Flexible footage support affects repeated use

Players may analyze more matches if they can use recordings from devices and workflows they already have.

**How to test:** Ask players how they currently record matches, what prevents them from recording regularly, and whether device or setup requirements cause them to stop.

### H14: Coaches need a review workflow distinct from the player experience

Coaches may value player comparison, timestamped findings, comments, and practice planning more than consumer-facing statistics or line calling.

**How to test:** Observe how coaches currently review footage and manage notes across multiple players. Identify steps that remain manual or time-consuming.

## What changed

Before this research, my initial concept centered on automatically producing match statistics and searchable clips from tennis video. I thought those features might be enough to define the product.

After reviewing the competitive landscape, I found that those capabilities are already established, especially in SwingVision. The initial concept demonstrates a real market but does not yet give my teammates or coach a strong reason to choose Ace Pro.

Because of this, I propose investigating a team-and-coach workflow built around evidence-backed pattern discovery: identify recurring match patterns, rank what matters, connect every conclusion to video, expose uncertainty, and help us decide what to work on next.

This differentiator remains a hypothesis. I should not treat it as the final positioning until my teammates and coach find it useful and direct competitor testing shows that existing products leave this need unmet.

## Open questions

- Do existing SwingVision users struggle to interpret or act on its statistics?
- What makes a tennis pattern important enough to prioritize?
- Can Ace Pro produce tactical conclusions reliably from ordinary footage?
- How should confidence be communicated without overwhelming the user?
- How much time will users spend correcting detections?
- Do players want recommendations, or would that feel less trustworthy than neutral evidence?
- Which parts of the workflow should be designed primarily for coaches?
- Is flexible device support a meaningful advantage or merely an expected feature?

## Next steps

- Test **SwingVision**, the closest direct competitor, using representative footage from one of our matches.
- Test **Wingfield**, the second competitor, through an available Wingfield court, demo, or product trial. If hands-on access is unavailable, document that constraint and complete a guided product walkthrough.
- For both competitor tests, record setup time, equipment requirements, supported footage, statistics, searchable clips, accuracy problems, correction options, coach-sharing features, player comparison, and whether the output suggests a useful next action.
- Write a short set of takeaways after each test: what worked well, what did not, what my teammates and coach would actually use, what remains manual, and what Ace Pro should learn rather than duplicate.
- Compare the two tests and decide whether the proposed interpretation and team-workflow gap actually exists.
- Interview current or former SwingVision users.
- Show my teammates and coach both a statistics dashboard and an evidence-backed prioritized insight.
- Ask whether either version would change a real practice or coaching decision for our team.
- Select one narrow pattern that could be detected and demonstrated technically.
- Avoid defining the MVP until the interpretation-gap hypothesis has evidence.
