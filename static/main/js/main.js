const navToggle = document.querySelector('.nav-toggle');
const navMenu = document.querySelector('.nav-menu');

if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
        const isOpen = navMenu.classList.toggle('is-open');
        navToggle.setAttribute('aria-expanded', String(isOpen));
    });
}

const modalOpenButtons = document.querySelectorAll('[data-modal-open]');
const modalCloseButtons = document.querySelectorAll('[data-modal-close]');

const setModalState = (modal, isOpen) => {
    if (!modal) {
        return;
    }

    modal.classList.toggle('is-open', isOpen);
    modal.setAttribute('aria-hidden', String(!isOpen));
    document.body.classList.toggle('modal-lock', isOpen);

    if (isOpen) {
        const firstField = modal.querySelector('input, textarea, button');
        if (firstField) {
            firstField.focus();
        }
    }
};

modalOpenButtons.forEach((button) => {
    button.addEventListener('click', () => {
        const modal = document.getElementById(button.dataset.modalOpen);
        setModalState(modal, true);
    });
});

modalCloseButtons.forEach((button) => {
    button.addEventListener('click', () => {
        setModalState(button.closest('.modal'), false);
    });
});

document.addEventListener('keydown', (event) => {
    if (event.key !== 'Escape') {
        return;
    }

    document.querySelectorAll('.modal.is-open').forEach((modal) => {
        setModalState(modal, false);
    });
});

document.querySelectorAll('.modal.is-open').forEach((modal) => {
    document.body.classList.add('modal-lock');
});

if (window.location.hash) {
    const modalFromHash = document.querySelector(window.location.hash);
    if (modalFromHash && modalFromHash.classList.contains('modal')) {
        setModalState(modalFromHash, true);
    }
}

const modalFromQuery = new URLSearchParams(window.location.search).get('modal');
if (modalFromQuery) {
    const modal = document.getElementById(modalFromQuery);
    if (modal && modal.classList.contains('modal')) {
        setModalState(modal, true);
    }
}

document.querySelectorAll('[data-event-time]').forEach((eventTime) => {
    const unixSeconds = Number(eventTime.dataset.eventTime);

    if (!Number.isFinite(unixSeconds) || unixSeconds <= 0) {
        return;
    }

    const eventDate = new Date(unixSeconds * 1000);
    const dateElement = eventTime.querySelector('[data-event-date]');
    const clockElement = eventTime.querySelector('[data-event-clock]');
    const zoneElement = eventTime.querySelector('[data-event-zone]');

    if (dateElement) {
        dateElement.textContent = new Intl.DateTimeFormat(undefined, {
            day: 'numeric',
            month: 'long',
        }).format(eventDate);
    }

    if (clockElement) {
        clockElement.textContent = new Intl.DateTimeFormat(undefined, {
            hour: '2-digit',
            minute: '2-digit',
        }).format(eventDate);
    }

    if (zoneElement) {
        zoneElement.textContent = new Intl.DateTimeFormat(undefined, {
            timeZoneName: 'short',
        })
            .formatToParts(eventDate)
            .find((part) => part.type === 'timeZoneName')?.value || '';
    }
});

document.querySelectorAll('.slot-pick-chip').forEach((chip) => {
    const checkbox = chip.querySelector('input[type="checkbox"]');

    if (!checkbox) {
        return;
    }

    const updateChip = () => {
        chip.classList.toggle('is-selected', checkbox.checked);
        chip.setAttribute('aria-pressed', String(checkbox.checked));
    };

    chip.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') {
            return;
        }

        event.preventDefault();
        checkbox.checked = !checkbox.checked;
        checkbox.dispatchEvent(new Event('change', { bubbles: true }));
    });

    checkbox.addEventListener('change', updateChip);
    updateChip();
});
