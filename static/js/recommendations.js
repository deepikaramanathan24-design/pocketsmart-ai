const jewelryForm = document.getElementById("jewelryForm");

if (jewelryForm) {
    jewelryForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData();

        formData.append(
            "user_id",
            document.getElementById("user_id").value
        );

        formData.append(
            "budget",
            document.getElementById("budget").value
        );

        formData.append(
            "jewelry_type",
            document.getElementById("jewelry_type").value
        );

        formData.append(
            "occasion",
            document.getElementById("occasion").value
        );

        formData.append(
            "style",
            document.getElementById("style").value
        );

        const imageInput = document.getElementById("outfit_image");

        if (imageInput && imageInput.files.length > 0) {
            formData.append("outfit_image", imageInput.files[0]);
        }

        const response = await fetch("/generate-jewelry", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        showResult(data);
    });
}