from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# Store the Owner in the session_state "vault" so it (and its pets/tasks)
# persists across Streamlit reruns. Only create it the first time.
if "owner" not in st.session_state:
    st.session_state["owner"] = Owner(name="Jordan", email="jordan@example.com")

owner = st.session_state["owner"]

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.divider()

# --- Add a Pet ---------------------------------------------------------
st.subheader("Add a Pet")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])
pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=2)

if st.button("Add pet"):
    # Owner.add_pet handles storing the new pet on the owner.
    new_pet = Pet(
        id=f"p{len(owner.pets) + 1}",
        name=pet_name,
        species=species,
        age=int(pet_age),
    )
    owner.add_pet(new_pet)
    st.success(f"Added {new_pet.name}!")

# The rerun after the button press redraws this list with the new pet.
if owner.pets:
    st.write("Current pets:", ", ".join(pet.name for pet in owner.pets))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a Task to a Pet ----------------------------------------------
st.subheader("Add a Task")
if not owner.pets:
    st.info("Add a pet first, then you can give it tasks.")
else:
    pet_names = [pet.name for pet in owner.pets]
    target_name = st.selectbox("Which pet?", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        times_per_day = st.number_input("Times per day", min_value=1, max_value=10, value=1)

    col4, col5, col6 = st.columns(3)
    with col4:
        priority_name = st.selectbox("Priority", [p.name for p in Priority], index=1)
    with col5:
        use_time = st.checkbox("Set preferred time", value=True)
    with col6:
        preferred = st.time_input("Preferred start", value=time(8, 0), disabled=not use_time)

    if st.button("Add task"):
        # Find the chosen pet, then Pet.add_task handles storing the task.
        target_pet = next(pet for pet in owner.pets if pet.name == target_name)
        target_pet.add_task(
            Task(
                description=task_title,
                duration_minutes=int(duration),
                times_per_day=int(times_per_day),
                time=preferred.strftime("%H:%M") if use_time else "",
                priority=Priority[priority_name],
            )
        )
        st.success(f"Added '{task_title}' to {target_name}!")

st.divider()

# --- Build Schedule ----------------------------------------------------
st.subheader("Today's Schedule")

if st.button("Generate schedule"):
    scheduler = Scheduler()
    occurrences = scheduler.build_day(owner)

    if not occurrences:
        st.caption("No pending tasks yet. Add some above.")
    else:
        # Time-ordered timeline (recurring tasks are expanded into slots).
        for occ in occurrences:
            flag = " 🔴" if occ.task.priority is Priority.HIGH else ""
            st.write(f"- {occ.label()}{flag}")

        total_minutes = sum(occ.task.duration_minutes for occ in occurrences)
        st.info(f"Total time needed today: {total_minutes} min")

        # Conflict detection: flag overlapping occurrences.
        conflicts = scheduler.find_conflicts(occurrences)
        if conflicts:
            st.warning(f"⚠️ {len(conflicts)} scheduling conflict(s) detected:")
            for first, second in conflicts:
                st.write(f"- **{first.label()}** overlaps **{second.label()}**")
        else:
            st.success("No scheduling conflicts. ✅")
