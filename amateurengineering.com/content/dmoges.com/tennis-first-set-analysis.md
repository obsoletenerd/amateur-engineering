---
Title: Tennis First Set Analysis
Date: 2025-12-01T13:51:13+11:00
Tags: data-analysis, tennis, statistics, python
Author: dmoges
AuthorURL: https://dmoges.com
Category: dmoges
Status: published
Cover: /images/placeholder.jpg
---

When watching the tennis one day, the commentator said something along the lines of "this player (it was Federer) wins more than 90% of matches when they win the first set".
This sounded impressive, however then my mind got a bit skeptical on whether or not it was actually better than most players.
After all, it's only a five set match, and it's first to three - having a 1-0 advantage would be massive, even if the two players were equally skilled.
Further, if the player was good enough to win the first set, they were probably the better player anyway.

So I did what any normal person would do and analysed 343,000 professional tennis matches to find out the truth.

Short answer: Players that win more than 90% of matches after taking the first set are rare, and this is better than a coin-flip null hypothesis, significantly so, but not really that much.

{{< theme-img src="/images/tennis/01_hero_insight.png" alt="Hero Insight" >}}

# Is it a coin-flip?

If we assume both players are exactly equal in skill, then each set is a 50/50 coin flip.
In a best-of-three match, if you win the first set, you only need to win one of the next two sets to win the match.
Further, if you win the second set, you win the match immediately.
So after winning the first set, the outcomes are:
- You win the second set (50% chance) → you win match
- You lose the second set (50% chance) → match goes to third set
  - In the third set, you have a 50% chance of winning

So overall, your chance of winning the match after taking the first set is:

$$P(win\ match | win\ first\ set) = P(win\ set\ 2) + P(lose\ set\ 2) * P(win\ set\ 3) = 0.5 + 0.5 * 0.5 = 0.75$$

In a five-set match, the logic is similar but you need to win two of the next three sets.
The outcomes are more complex, but the process is the same and the final probability is:

$$P(win\ match | win\ first\ set) = 0.6875$$

Now, the 90% figure I put above is from my own poor memory, but it was in the range of 90+-ish% approximately, sort of.
So that means that yes, winning the first set does give you a significant advantage over the expected 68.75% or 75% chance of winning the match if both players were equal.


## What does the data say?

I analysed more than 300,000 matches from both the ATP and WTA tours, from [Jeff Sackmann's tennis repositories](https://github.com/JeffSackmann/tennis_atp).
I removed any non-3 or 5-set matches, as well as retirements, walkovers, and incomplete matches.
Overall, the win rates after taking the first set were as follows:
- Overall: 82.8% (343,000 matches)
- Best-of-3: 83.3% (301,809 matches)
- Best-of-5: 78.8% (41,190 matches)
- Men's (ATP): 81.4% (189,379 matches)
- Women's (WTA): 84.5% (153,620 matches)

So what we see is a true improvement in all the above categories, more than the chance rate.

{{< theme-img src="/images/tennis/02_gender_comparison.png" alt="Gender Comparison" >}}

Women don't play best-of-five matches, but for men, there is a difference between best-of-three and best-of-five matches, with best-of-five matches having a lower win rate after taking the first set (78.8% vs 83.3%).

{{< theme-img src="/images/tennis/08_format_comparison.png" alt="Format Comparison" >}}

Interestingly, while best-of-5 shows a *lower* absolute win rate, the difference from the null hypothesis is actually *larger* (+10.0pp vs +8.3pp). This suggests the additional sets provide more opportunity for the better player to assert dominance.

Interestingly, there seems to be a *downward trend* in win rates after taking the first set over time.
In the 1960s, the win rate was 85.1%, while in the 2010s it was 81.2%.
This suggests that players are getting better at comebacks over time, possibly due to improved fitness, coaching, or mental training.

{{< theme-img src="/images/tennis/03_decade_trend.png" alt="Decade Trend" >}}

| Decade | Women | Men |
|--------|-------|-----|
| 1960s | 87.67% | 82.93% |
| 1980s | 84.90% | 81.56% |
| 2000s | 83.75% | 81.11% |
| 2020s | 82.11% | 80.40% |


### The Underdog Effect
{{< theme-img src="/images/tennis/04_underdog_transformation.png" alt="Underdog Analysis" >}}

One of the interesting aspects of tournament play is that great players are *often* playing much weaker players for at least the first half of the tournament.
So the above results are likely heavily skewed by the fact that the favourite player is often much better than the underdog.
To analyse this, I looked at matches where there was a clear favourite and underdog, defined by ranking difference.

In these matches, the overall upset rate (underdog winning) was 33%.
However, when looking at first set winners, it changes dramatically if the underdog can take the first set.
When the underdog gets the first set, they go on to win the match 70.4% of the time.
Conversely, if the favourite takes the first set, the underdog only wins 11.5% of the time.
This means that the first set changes the underdog's probability of winning
**First set transforms upset probability by +37 percentage points.**

When the gap between players is small (1-10 ranks), the underdog wins 17% of matches overall, but if they take the first set, they win 77% of the time (+60pp).
When the gap is large (201+ ranks), the underdog wins only 7% of matches overall, but if they take the first set, they win 60% of the time (+53pp).
This shows that the first set is crucial for underdogs, regardless of ranking gap.

{{< theme-img src="/images/tennis/05_ranking_gap_impact.png" alt="Ranking Gap Impact" >}}

| Gap (Ranks) | Matches | Fav wins after 1st | Und wins after 1st | Gap Impact |
|-------------|---------|--------------------|--------------------|------------|
| 1-10 | 33,414 | 82.9% | 77.2% | +60.1pp |
| 11-20 | 30,391 | 85.8% | 74.3% | +60.1pp |
| 21-50 | 69,884 | 87.6% | 71.3% | +58.9pp |
| 51-100 | 57,315 | 90.2% | 67.0% | +57.1pp |
| 101-200 | 31,082 | 91.2% | 64.0% | +55.2pp |
| 201+ | 18,610 | 92.9% | 59.7% | +52.6pp |


### Comeback Kings and Queens

As an Aussie, I distinctly remember Lleyton Hewitt's reputation as a tenacious player who often came back from behind.
He never gave up, and this was reflected in his match statistics.
So who are the best comeback players in tennis history?

{{< theme-img src="/images/tennis/06_comeback_legends.png" alt="Comeback Kings" >}}

#### Best-of-3 Comeback Leaders

| Rank | Player | Overall Win % | Comeback % | Sample Size |
|------|--------|---------------|------------|-------------|
| 1 | Margaret Court | 91.1% | **55.5%** | 110 losses |
| 2 | Serena Williams | 86.1% | 48.5% | 206 losses |
| 3 | Steffi Graf | 89.3% | 47.1% | 155 losses |
| 4 | Rod Laver | 78.7% | 46.4% | 153 losses |
| 5 | Chris Evert | 89.9% | 45.5% | 231 losses |
| 6 | Justine Henin | 82.1% | 44.4% | 124 losses |
| 7 | Jimmy Connors | 82.9% | 42.7% | 279 losses |
| 8 | Novak Djokovic | 81.6% | 41.0% | 222 losses |
| 9 | Pete Sampras | 76.5% | 40.7% | 194 losses |
| 10 | John McEnroe | 81.9% | 40.2% | 189 losses |

#### Best-of-5 Comeback Leaders (Grand Slams)

| Rank | Player | Overall Win % | Comeback % | Sample Size |
|------|--------|---------------|------------|-------------|
| 1 | Bjorn Borg | 87.1% | **60.0%** | 70 losses |
| 2 | Rod Laver | 83.0% | 57.7% | 52 losses |
| 3 | Boris Becker | 79.5% | 55.3% | 76 losses |
| 4 | Alexander Zverev | 73.4% | 54.5% | 44 losses |
| 5 | Rafael Nadal | 88.6% | 53.8% | 78 losses |
| 6 | Novak Djokovic | 88.9% | 53.8% | 91 losses |
| 7 | Ivan Lendl | 80.3% | 53.3% | 105 losses |
| 8 | Pete Sampras | 81.2% | 50.6% | 79 losses |
| 9 | Carlos Alcaraz | 85.1% | 50.0% | 18 losses |
| 10 | Andre Agassi | 78.8% | 47.0% | 100 losses |

This naturally leads to the question of who are the best players at "locking in" a match after winning the first set.

{{< theme-img src="/images/tennis/07_lockin_champions.png" alt="Lock-in Champions" >}}

#### Best-of-3 Lock-in Leaders

| Rank | Player | Overall | Lock-in | Advantage |
|------|--------|---------|---------|-----------|
| 1 | Chris Evert | 89.9% | **98.1%** | +8.3pp |
| 2 | Margaret Court | 91.1% | 97.9% | +6.8pp |
| 3 | Linda Tuero | 69.4% | 97.5% | +28.1pp |
| 4 | Steffi Graf | 89.3% | 97.1% | +7.8pp |
| 5 | Evonne Goolagong | 82.1% | 96.6% | +14.4pp |
| 6 | Martina Navratilova | 86.7% | 96.3% | +9.6pp |
| 7 | Serena Williams | 86.1% | 96.1% | +10.0pp |
| 8 | Monica Seles | 83.3% | 95.7% | +12.3pp |
| 9 | Bjorn Borg | 80.6% | 95.7% | +15.0pp |
| 10 | Novak Djokovic | 81.6% | 95.6% | +14.1pp |

#### Best-of-5 Lock-in Leaders (Grand Slams)

| Rank | Player | Overall | Lock-in | Advantage |
|------|--------|---------|---------|-----------|
| 1 | Novak Djokovic | 88.9% | **98.0%** | +9.1pp |
| 2 | Rafael Nadal | 88.6% | 97.7% | +9.0pp |
| 3 | Bjorn Borg | 87.1% | 97.3% | +10.2pp |
| 4 | Jimmy Connors | 81.3% | 94.3% | +13.1pp |
| 5 | Roger Federer | 84.6% | 94.2% | +9.6pp |
| 6 | Andy Murray | 78.9% | 94.0% | +15.1pp |
| 7 | John McEnroe | 81.4% | 93.1% | +11.7pp |
| 8 | Andre Agassi | 78.8% | 92.9% | +14.1pp |
| 9 | Rod Laver | 83.0% | 92.6% | +9.7pp |
| 10 | Pete Sampras | 81.2% | 92.5% | +11.3pp |

There is massive overlap here, indicating that champions are good regardless of match situation.


## Conclusions

Overall, while my alarm bells went off at the initial claim of "90% of matches won after taking the first set", it turns out that players that do have this level of dominance are rare, and that winning the first set does provide a significant advantage over the null hypothesis of equal skill.
The greats do tend to "lock-in" matches after taking the first set, and underdogs can massively improve their chances by taking the first set.

There are *many* compound factors at play here, including player skill, fitness, mental toughness, and match conditions.
Further, if an underdog won the first set, was the other player (even slightly) injured or fatigued?
These are all factors that would be interesting to explore further.

Get in touch if you want the code, but I recommend playing with it yourself and exploring further.