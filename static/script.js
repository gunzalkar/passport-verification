document.getElementById('uploadButton').addEventListener('click', () => {
    document.getElementById('fileInput').click();
});

document.getElementById('fileInput').addEventListener('change', async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('loader').style.display = 'block';
    document.getElementById('errorMessage').textContent = '';

    fetch('/upload-image/', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to process the image. Please try again.');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        document.getElementById('uploadContainer').style.display = 'none';
        displayExtractedData(data);
    })
    .catch(error => {
        document.getElementById('errorMessage').textContent = error.message;
        document.getElementById('uploadContainer').style.display = 'block';
    })
    .finally(() => {
        document.getElementById('loader').style.display = 'none';
    });
});

document.getElementById('cameraButton').addEventListener('click', async () => {
    const video = document.getElementById('camera');
    const cameraView = document.getElementById('cameraView');
    const canvas = document.getElementById('canvas');
    const takePhotoButton = document.getElementById('takePhotoButton');
    const cancelButton = document.getElementById('cancelButton');
    // Hide upload container
    cameraView.style.display = 'flex';
    try {
        const constraints = {
            video: {
                facingMode: 'environment'  // Use back camera
            }
        };
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;
        video.style.display = 'block';
        takePhotoButton.style.display = 'block';
        cancelButton.style.display = 'block';

        takePhotoButton.addEventListener('click', () => {
            const context = canvas.getContext('2d');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            const dataURL = canvas.toDataURL('image/png');
            video.style.display = 'none';
            stream.getTracks().forEach(track => track.stop());
            takePhotoButton.style.display = 'none';
            cancelButton.style.display = 'none';

            const blob = dataURLToBlob(dataURL);
            const file = new File([blob], 'photo.png', { type: 'image/png' });

            const formData = new FormData();
            formData.append('file', file);

            document.getElementById('loader').style.display = 'block';
            document.getElementById('errorMessage').textContent = '';
            cameraView.style.display = 'none';

            fetch('/upload-image/', {
                method: 'POST',
                body: formData,
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to process the image. Please try again.');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                document.getElementById('uploadContainer').style.display = 'none';
                displayExtractedData(data);
            })
            .catch(error => {
                document.getElementById('errorMessage').textContent = error.message;
                document.getElementById('uploadContainer').style.display = 'block';
            })
            .finally(() => {
                document.getElementById('loader').style.display = 'none';
            });

        });

        cancelButton.addEventListener('click', () => {
            stream.getTracks().forEach(track => track.stop());
            video.style.display = 'none';
            takePhotoButton.style.display = 'none';
            cancelButton.style.display = 'none';
            cameraView.style.display = 'none';
            document.getElementById('uploadContainer').style.display = 'block'; // Show upload container on cancel
        });
    } catch (error) {
        document.getElementById('errorMessage').textContent = 'Failed to access the camera. Please ensure you have granted permission.';
        document.getElementById('uploadContainer').style.display = 'block'; // Show upload container on error
    }
});

function dataURLToBlob(dataURL) {
    const binary = atob(dataURL.split(',')[1]);
    const array = [];
    for (let i = 0; i < binary.length; i++) {
        array.push(binary.charCodeAt(i));
    }
    return new Blob([new Uint8Array(array)], { type: 'image/png' });
}

function displayExtractedData(data) {
    const container = document.getElementById('extractedData');
    container.innerHTML = '';

    for (const [key, value] of Object.entries(data.data)) {
        const item = document.createElement('div');
        item.className = 'result-item';

        const keyLabel = document.createElement('div');
        keyLabel.className = 'key-label';
        keyLabel.textContent = key;

        const valueContainer = document.createElement('div');
        valueContainer.className = 'value-container';

        const val = document.createElement('div');
        val.className = 'value';
        val.textContent = value.value;

        const statusDot = document.createElement('span');
        statusDot.className = `status-dot ${value.status ? 'true' : 'false'}`;

        valueContainer.appendChild(val);
        valueContainer.appendChild(statusDot);

        item.appendChild(keyLabel);
        item.appendChild(valueContainer);
        container.appendChild(item);
    }

    if (data.face_image) {
        const faceImg = document.getElementById('photo');
        faceImg.src = `data:image/jpeg;base64,${data.face_image}`;
        document.getElementById('photoContainer').style.display = 'block';
    } else {
        document.getElementById('photoContainer').style.display = 'none';
    }

    if (data.mrz_image) {
        const mrzImg = document.getElementById('mrz');
        mrzImg.src = `data:image/jpeg;base64,${data.mrz_image}`;
        mrzImg.style.width = '100%';  // Ensure the image spans the width of the container
        document.getElementById('mrzContainer').style.display = 'block';
    } else {
        document.getElementById('mrzContainer').style.display = 'none';
    }

    document.getElementById('resultContainer').style.display = 'block';

    // Ensure scrolling to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.querySelector('html').scrollTop = 0;
    document.body.scrollTop = 0;
}

document.getElementById('backButton').addEventListener('click', () => {
    document.getElementById('resultContainer').style.display = 'none';
    document.getElementById('uploadContainer').style.display = 'block';
});
