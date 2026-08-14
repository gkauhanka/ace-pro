# Initial Discovery

**Date:** August 12, 2026  
**Phase:** Discovery

## Goal

Explore whether a tennis match video analyzer solves a useful problem, identify who might use it, and determine what information would be worth extracting before building the product.

The initial concept is:

**Match video → AI analysis → statistics and useful clips**

## What I did

Outlined the possible problem, users, features, product hypotheses, risks, and technical unknowns. I also defined interview questions, comparable-product research, and a first technical experiment to validate the idea.

## Possible problem

Players usually know when they make an individual mistake, but it is harder to see patterns across a full match, such as:

- Forehand and backhand consistency
- First- and second-serve percentages
- Net approach frequency and success
- Cross-court versus down-the-line shots
- Changes between matches

The product should probably not begin as a full "AI coach." A clearer initial promise is:

**"Here is what actually happened in your match."**

## Possible users

### Player

The player is the most obvious first user. Possible value includes:

- Seeing objective match statistics
- Comparing performance between matches
- Confirming whether something that felt good or bad actually was
- Finding recurring weaknesses
- Quickly rewatching mistakes
- Understanding patterns of play

The main product question is whether this would be useful enough for a player to use repeatedly.

### Coach

A coach could use the product to:

- Review more information about each player
- Find weaknesses without watching every point manually
- Identify team-wide weaknesses
- Decide what needs more practice
- Search video for particular mistakes
- Compare players and matches

This needs validation through direct conversations with coaches about what they currently review and what would change a coaching decision.

## Important discovery principle

Do not choose features only because they appear technically possible. First determine:

- What would actually be useful?
- Who would care?
- What information would they want?
- Can AI realistically extract that information?

## Possible MVP statistics

Start with approximately three to five statistics chosen by usefulness and technical difficulty:

- Forehand in/out percentage
- Backhand in/out percentage
- First-serve percentage
- Second-serve percentage
- Net approaches and success rate
- Cross-court versus down-the-line shots
- Number of points
- Errors by type

## Searchable video and annotations

Statistics should have supporting evidence. If the product reports eight forehand errors, the user should be able to open those eight moments.

Each detected event could contain:

- Timestamp
- Short clip
- Event type
- AI result
- Confidence
- User correction when the result is wrong

Searches such as "show all forehand errors" or "show all missed first serves" may be among the strongest features because they avoid manually reviewing an entire match.

## User correction

The AI will probably not be perfect. A correction workflow could make imperfect analysis usable:

- Automatically count high-confidence detections
- Ask the user to verify low-confidence detections
- Let the user correct classifications
- Recalculate statistics after corrections

## Footage scope

Short clips are probably insufficient for meaningful statistics because a brief sequence may not represent the player's overall performance. Full-match footage should provide a better sample.

Match footage may also be more valuable than practice footage because it captures real pressure, points, opponents, and decisions. Practice footage could be supported later.

## Technical unknowns

The largest technical risk is whether AI can understand normal tennis footage well enough. Tests should cover:

- Which player hit the ball
- Forehand versus backhand
- First versus second serve
- Serve in or out
- Ball in or out
- Ball hitting the net
- Point winner
- Point start and end
- Net approaches
- Cross-court versus down-the-line shots

Camera angle will matter. Potential problems include a ball that is too small, unclear court lines, occlusion by players, a camera that is too low or distant, and incomplete court coverage. A phone or GoPro attached to the fence behind the baseline is one setup to test.

## Product hypotheses

- **H1:** Players would find automatic match statistics useful. This is not yet validated.
- **H2:** Comparing statistics between matches may be more valuable than analyzing only one match.
- **H3:** Full-match footage provides more useful information than short clips.
- **H4:** Real match footage is more useful than controlled practice footage.
- **H5:** Searchable clips may be valuable even if advanced coaching analysis is not possible.
- **H6:** Players and coaches probably want different information.
- **H7:** User correction could compensate for imperfect AI detection.

## Key findings

- The idea has two separate validation needs: user value and technical feasibility.
- Players are the likely primary users; coaches are a possible secondary group.
- Match statistics provide a more focused starting point than broad AI coaching.
- Searchable clips could be as valuable as, or more valuable than, aggregate statistics.
- Full-match footage is likely more informative than short clips or controlled practice footage.
- A correction workflow may allow useful results without requiring perfect AI accuracy.
- The MVP should contain only a few validated statistics.

## Main risks

### Product risk

Players may find the statistics interesting once but not valuable enough for repeated use. Interviews are needed to understand what would create ongoing value.

### Technical risk

Current AI may not reliably detect enough events from ordinary tennis footage, especially ball in/out, shot direction, point winner, and serve result. Quick technical tests are needed before building the full application.

## Discovery interviews

### Coach

Talk to Gary. Avoid asking only whether he would use the product. Ask:

- What do you pay attention to when watching players?
- How do you identify weaknesses?
- Do you track statistics or keep player notes?
- How do you decide what players should practice?
- Do you watch match video?
- What is time-consuming or frustrating about reviewing video?
- What information would you want automatically from a match?
- What statistics would change a coaching decision?

### Players

Talk to at least one or two players without leading them toward the current idea. Ask:

- Do you track statistics?
- What do you want to know after a match?
- Do you watch yourself play?
- What do you normally notice about your game?
- Would comparing matches be useful?
- Which statistics would be interesting?
- What would make you use this more than once?

## Comparable products

Research sports analytics products, especially basketball systems that track shot locations, makes and misses, shooting percentages, and player tendencies. Determine why players and coaches use them and whether the same value could apply to tennis.

## First technical experiment

Before building the architecture, interface, or database, test existing AI/video models on several short tennis clips.

| Test | Result to check |
|---|---|
| Forehand/backhand | Did the AI classify it correctly? |
| Serve in/out | Was the result correct? |
| Point winner | Was the winner correct? |
| Ball hit net | Was the event detected correctly? |
| Net approach | Was the approach detected correctly? |
| Point start/end | Were the boundaries correct? |

For every test, record:

- Model or tool
- Video
- Camera angle
- Question
- Expected answer
- AI answer
- Correct or incorrect
- Notes

The experiment should answer: **What can current AI reliably understand from tennis video?**

## What changed

Before this discovery activity, the idea was broadly an AI tennis match analyzer and could have expanded immediately toward coaching or technique advice.

After mapping the users, value, risks, and technical unknowns, the current direction is narrower: begin with players as the primary user, focus on full-match statistics backed by searchable clips, and treat coaches as a secondary user group.

Because of this, the project should validate user needs and test video-model feasibility before committing to architecture, a final feature set, or a full AI-coaching experience.

## Open questions

- Which statistics are valuable enough to influence player or coach decisions?
- Would players use the product repeatedly?
- Are cross-match comparisons more valuable than a single-match report?
- Which tennis events can current models detect reliably?
- What camera setup provides sufficient video quality?
- How much user correction is acceptable?
- Should searchable clips be prioritized over advanced aggregate statistics?

## Next steps

- Talk to Gary about what information is useful to a coach.
- Talk to at least one other tennis player.
- Research comparable sports analytics products.
- Choose three to five initial statistics to test.
- Find or record representative tennis footage.
- Test multiple AI/video models.
- Document what each model can and cannot detect.
- Use the findings to determine MVP scope.

## Current status

The project remains in discovery, with no final feature set. Two questions must be validated before deciding what to build:

1. Is the information useful to players and coaches?
2. Can it be extracted reliably enough from normal tennis video?
