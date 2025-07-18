// This script creates a simple calendar that displays the current month and allows navigation between months.
// It highlights the current date and adjusts the first day of the week to Monday (Euro style).
// Source : https://dev.to/wizdomtek/creating-a-dynamic-calendar-using-html-css-and-javascript-29m
//
// Other more sophisticated option : https://vanilla-calendar.pro/
//
const calendarDates = document.querySelector('.calendar-dates');
const monthYear = document.getElementById('month-year');
const prevMonthBtn = document.getElementById('prev-month');
const nextMonthBtn = document.getElementById('next-month');

let currentDate = new Date();
let currentMonth = currentDate.getMonth();
let currentYear = currentDate.getFullYear();

const months = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

function renderCalendar(month, year) {
    calendarDates.innerHTML = '';
    monthYear.textContent = `${months[month]} ${year}`;
  
    // Get the first day of the month
    const firstDayUS = new Date(year, month, 1).getDay();

    // Adjust for Euro calendar (Monday as first day)
    const firstDayEuro = firstDayUS === 0 ? 6 : firstDayUS - 1;
    // Get the number of days in the month
    const daysInMonth = new Date(year, month + 1, 0).getDate();
  
    // Create blanks for days of the week before the first day
    for (let i = 0; i < firstDayEuro; i++) {
    //for (let i = 1; i <= firstDayEuro; i++) {
      const blank = document.createElement('div');
      calendarDates.appendChild(blank);
    }
  
  // Get today's date
  const today = new Date();

  // Populate the days
  for (let i = 1; i <= daysInMonth; i++) {
    const day = document.createElement('div');
    day.textContent = i;

    // Highlight today's date
    if (
      i === today.getDate() &&
      year === today.getFullYear() &&
      month === today.getMonth()
    ) {
      day.classList.add('current-date');
    }

    calendarDates.appendChild(day);
    }
  }

  renderCalendar(currentMonth, currentYear);
  
  prevMonthBtn.addEventListener('click', () => {
    currentMonth--;
    if (currentMonth < 0) {
      currentMonth = 11;
      currentYear--;
    }
    renderCalendar(currentMonth, currentYear);
  });
  
  nextMonthBtn.addEventListener('click', () => {
    currentMonth++;
    if (currentMonth > 11) {
      currentMonth = 0;
      currentYear++;
    }
    renderCalendar(currentMonth, currentYear);
  });


  