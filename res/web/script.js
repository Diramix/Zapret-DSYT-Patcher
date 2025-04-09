const developers = [
  { apiUrl: 'https://api.github.com/users/diramix', id: 'Diramix' },
  { apiUrl: 'https://api.github.com/users/WolfySoCute', id: 'WolfySoCute' }
];

const fetchDeveloperData = (dev) => {
  return fetch(dev.apiUrl)
    .then(response => response.ok ? response.json() : null)
    .then(data => {
      const nicknameElement = document.querySelector(`.nickname#${dev.id}`);
      if (!nicknameElement) return;

      const content = data && data.login ? data.login : 'Unknown';
      const linkElement = document.createElement(content === 'Unknown' ? 'span' : 'a');

      if (content !== 'Unknown') {
        linkElement.href = `https://github.com/${data.login}`;
        linkElement.target = '_blank';
      }

      linkElement.textContent = content;
      nicknameElement.appendChild(linkElement);
    })
    .catch(() => handleError(dev.id));
};

const handleError = (id) => {
  const nicknameElement = document.querySelector(`.nickname#${id}`);
  if (nicknameElement) {
    const span = document.createElement('span');
    span.textContent = 'Unknown';
    nicknameElement.appendChild(span);
  }
};

const fetchReleaseData = () => {
  return fetch('https://api.github.com/repos/Flowseal/zapret-discord-youtube/releases/latest')
    .then(response => {
      if (!response.ok) {
        throw new Error('Failed to fetch release data');
      }
      return response.json();
    })
    .then(data => updateDescription(data.body))
    .catch(handleReleaseError);
};

const updateDescription = (description) => {
  const converter = new showdown.Converter({ simplifiedAutoLink: true, openLinksInNewWindow: true });
  const htmlDescription = converter.makeHtml(description || '');
  const descriptionElement = document.querySelector('.description');

  if (descriptionElement) {
    descriptionElement.innerHTML = htmlDescription;
  }
};

const handleReleaseError = () => {
  console.error('Error fetching release data');

  const descriptionElement = document.querySelector('.description');
  if (descriptionElement) {
    descriptionElement.textContent = 'Unknown';
    descriptionElement.style.color = 'red';
  }

  const body2Element = document.querySelector('.body2');
  if (body2Element) {
    body2Element.style.background = 'linear-gradient(180deg, #F00 0%, #000d1a 100%)';
  }

  const latestElements = document.querySelectorAll('#ab_latest');
  latestElements.forEach(element => element.style.display = 'none');

  const skillIssuesElements = document.querySelectorAll('.skill_issues');
  skillIssuesElements.forEach(element => element.style.display = 'none');
};

developers.forEach(fetchDeveloperData);
fetchReleaseData();
