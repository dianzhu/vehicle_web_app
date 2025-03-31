function onIndividualRadioButtonClick() {
    document.getElementById("customerIdLabel").innerText = "Driver's License Number*";

    const individualInfo = document.getElementById("individualInfo");
    const businessInfo = document.getElementById("businessInfo");

    hideElement(businessInfo);
    showElement(individualInfo);
    addRemoveRequiredFormInputs(individualInfo, businessInfo);

}

function onBusinessRadioButtonClick() {
    document.getElementById("customerIdLabel").innerText = "Tax ID*";

    const individualInfo = document.getElementById("individualInfo");
    const businessInfo = document.getElementById("businessInfo");

    hideElement(individualInfo);
    showElement(businessInfo);
    addRemoveRequiredFormInputs(businessInfo, individualInfo);

}

function addRemoveRequiredFormInputs(addParentDiv, removeParentDiv) {
    const addElems = addParentDiv.getElementsByTagName("input");
    const removeElems = removeParentDiv.getElementsByTagName("input");
    for (const elem of addElems) {
        requiredFormElement(elem);
    }
    for (const elem of removeElems) {
        notRequiredFormElement(elem);
    }
}