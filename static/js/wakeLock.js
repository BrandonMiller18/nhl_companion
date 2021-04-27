
const checkbox = document.querySelector('#wakeLock');
const statusElem = document.querySelector('#wakeLockStatus')

const updateUI = (status = 'acquired') => {
  const acquired = status === 'acquired' ? true : false;
  checkbox.dataset.status = acquired ? 'on' : 'off';
  checkbox.checked = acquired ? true : false;
  statusElem.textContent = `Wake Lock ${acquired ? 'is active!' : 'is off.'}`;
}

// test support
let isSupported = false;

if ('wakeLock' in navigator) {
    isSupported = true;
    statusElem.textContent = 'Wake lock API is supported in your browser!';
} else {
    checkbox.disabled = true;
    statusElem.textContent = 'Wake lock is not supported by this browser.';
}

if (isSupported ) {
    // create a reference for the wake lock
    let wakeLock = null;

    // create an async function to request a wake lock
    const requestWakeLock = async () => {
        try {
            wakeLock = await navigator.wakeLock.request('screen');

            // change up our interface to reflect wake lock active
            updateUI()

            // listen for our release event
            wakeLock.onrelease = function(ev) {
                console.log(ev);
            }
            wakeLock.addEventListener('release', () => {
            // if wake lock is released alter the button accordingly
                updateUI('released');
            });

            console.log(wakeLock)

        } catch (err) {
            // if wake lock request fails - usually system related, such as battery
            checkbox.checked = false;
            statusElem.textContent = `${err.name}, ${err.message}`;
        }
    } // requestWakeLock()

    // toggle
    checkbox.addEventListener('click', () => {
        // if wakelock is off request it
        if (checkbox.dataset.status === 'off') {
          requestWakeLock()
        } else { // if it's on release it
          wakeLock.release()
            .then(() => {
              wakeLock = null;
            })
        }
    })

}