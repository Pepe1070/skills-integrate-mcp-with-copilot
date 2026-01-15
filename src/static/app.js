document.addEventListener("DOMContentLoaded", () => {
  const registerForm = document.getElementById("register-form");
  const regMessageDiv = document.getElementById("reg-message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Populate activities list
      activities.forEach((activity) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = activity.max_participants - activity.current_participants;

        activityCard.innerHTML = `
          <h4>${activity.name}</h4>
          <p>${activity.description}</p>
          <p><strong>Schedule:</strong> ${activity.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = activity.id;
        option.textContent = activity.name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    // Removed for now
  }

  // Handle register form submission
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("reg-email").value;
    const firstName = document.getElementById("first-name").value;
    const lastName = document.getElementById("last-name").value;
    const password = document.getElementById("password").value;

    try {
      const response = await fetch("/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          first_name: firstName,
          last_name: lastName,
          password,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        regMessageDiv.textContent = "Registration successful!";
        regMessageDiv.className = "success";
        registerForm.reset();
      } else {
        regMessageDiv.textContent = result.detail || "Registration failed";
        regMessageDiv.className = "error";
      }

      regMessageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        regMessageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      regMessageDiv.textContent = "Failed to register. Please try again.";
      regMessageDiv.className = "error";
      regMessageDiv.classList.remove("hidden");
      console.error("Error registering:", error);
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
