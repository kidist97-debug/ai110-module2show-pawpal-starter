# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  My initial UML design involves 5 classes, Owner, Pet, CareTask, Planne and Daily-plan. There is a one-to-many relationship between the owner and the pet (one owner and multiple pets) and the pet and the CareTask. DailyPlan is associated with a Pet. The Planner depends on Pet and Owner as inputs and creates a DailyPlan as output.


- What classes did you include, and what responsibilities did you assign to each?
  I included 5 classes mentioned above. The pet class has demographic information about the pet. The owner class also has demographic information about the owner and availability to take care of their pet/s and budget for the pets. The careTask class has information about each of the care tasks and the pet they are assigned to. The planner class takes the pet and owner as inputs and generates daily plans.
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

1. How often a task happens

Before: each task just said something like "daily" as a label.
Now: each task records how many times a day it happens, and can add up the total time it needs.
Why: The assistant needs to actually count minutes. If you walk the dog twice a day for 15 minutes, that's 30 minutes of your day — not 15. The old way couldn't add that up correctly; now it can.
2. Planning for the whole household at once

Before: the assistant made a plan for one pet at a time.
Now: it looks at all your pets together and builds each pet's plan from your single pool of free time.
Why: Your free time is shared across every pet. The old way gave each pet your full free time — so with three pets, it acted like you had three times as many hours as you really do. Now it can't promise more than you actually have, and it fairly decides which pet's tasks come first when time runs short.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
conflict_warnings() only catches exact start-time matches, not overlapping durations
- Why is that tradeoff reasonable for this scenario?
Pet owners set tasks at round times (08:00, 12:00), so exact-time clashes are the common case. It's also just a warning, not an enforced rule — if it misses a partial overlap, the owner still sees the full timeline and can adjust. For a busy pet owner, a simple, fast check that flags the obvious conflicts beats a heavier duration-aware one. And find_conflicts() already exists if we want to upgrade later.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI to brain storm designs, get feedback on my drafts and debug codes that weren't working well.

- What kinds of prompts or questions were most helpful?
prompts asking for improvement ideas were helpful as they allow the AI to work on what I have already built on. It allowed me to have agency on the code.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
Some class suggestions it was giving me were complicated 
- How did you evaluate or verify what the AI suggested?
I try to fit the suggestions in the bigger picture of the project, if they are too complicated or missing something important from the given prompts, I rejected the sugegstions.
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
Class bulding was the most satisfying as it was the base of the project.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
I would add some more classes and simplify the current class relationships

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
It is important to critically examine AI suggested feature as they mostly involve things beyong the scope of what we are building.
