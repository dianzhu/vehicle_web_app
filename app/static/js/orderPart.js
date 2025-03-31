function onExistingRadioButtonClick() {

    const po = document.getElementById("po");

    showElement(po);
    addRequiredFormInputs(po);
}

function onNewRadioButtonClick() {

    const po = document.getElementById("po");

    hideElement(po);
    removeRequiredFormInputs(po);

}

function addRequiredFormInputs(addParentDiv) {
    const addElems = addParentDiv.getElementsByTagName("input");
    for (const elem of addElems) {
        requiredFormElement(elem);
    }
}

function removeRequiredFormInputs(removeParentDiv) {
    const removeElems = removeParentDiv.getElementsByTagName("input");
    for (const elem of removeElems) {
        notRequiredFormElement(elem);
    }
}

function onAddPartClick() {
    const part = document.getElementById("part");
    const newPart = part.cloneNode(true);
    newPart.id = "newPart";
    newPart.hidden = false;
    part.before(newPart);
    document.getElementById("removePartButton").hidden = false;
}

function onRemovePartClick() {
    const parts = document.getElementById("parts");
    if (parts.children.length > 2) parts.children[parts.children.length - 2].remove();
    if (parts.children.length <= 2) document.getElementById("removePartButton").hidden = true;
}

function onFormSubmit() {
    const parts = document.getElementById("parts");
    const part = document.getElementById("part");
    const backUpPart = part.cloneNode(true);
    part.remove();
    document.getElementById("partsForm").submit();
}
