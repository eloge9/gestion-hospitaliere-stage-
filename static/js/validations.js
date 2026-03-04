// Example starter JavaScript for disabling form submissions if there are invalid fields
(() => {
  "use strict";

  // Fetch all the forms we want to apply custom Bootstrap validation styles to
  const forms = document.querySelectorAll(".needs-validation");

  // Loop over them and prevent submission
  Array.from(forms).forEach((form) => {
    form.addEventListener(
      "submit",
      (event) => {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }

        form.classList.add("was-validated");
      },
      false
    );
  });
})();

function setDeleteUrl(doctorId) {
  const url = `/admin/supprimer_docteur/${doctorId}`;
  const confirmBtn = document.getElementById("confirmDeleteBtn");
  if (confirmBtn) {
    confirmBtn.setAttribute("href", url);
  }
}
function updateDeleteLink(button) {
  const adminId = button.getAttribute("data-id");
  const deleteUrl = `/admin/supprimer/${adminId}`; // Chemin exact selon ta route Flask
  document.getElementById("confirmDeleteBtn").setAttribute("href", deleteUrl);
}
