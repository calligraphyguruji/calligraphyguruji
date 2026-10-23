// Deterministic protocol fixture. Never used by the profile generator in Actions.
const http = require('http');
let retryCalls = 0;
http.createServer((req, res) => {
  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    res.setHeader('Content-Type', 'application/json');
    const route = req.url.split('/').pop();
    if (route === 'auth') { res.writeHead(401); return res.end('{}'); }
    if (route === 'rate') { res.writeHead(429, {'Retry-After': '120'}); return res.end('{}'); }
    if (route === 'server-error' || (route === 'retry' && retryCalls++ === 0)) {
      res.writeHead(503); return res.end('<html>Unavailable</html>');
    }
    if (route === 'malformed') return res.end('{');
    if (route === 'graphql-error') return res.end(JSON.stringify({errors: [{type: 'FORBIDDEN'}]}));
    if (!['graphql', 'retry'].includes(route)) { res.writeHead(501); return res.end('{}'); }
    const request = JSON.parse(body);
    if (req.method !== 'POST' || req.headers.authorization !== 'Bearer test-only' ||
        !request.query.includes('contributionCalendar') || !request.variables.from.endsWith('T00:00:00Z')) {
      res.writeHead(400); return res.end('{}');
    }
    const days = Array.from({length: 365}, (_, i) => ({
      date: new Date(Date.parse('2025-10-24T00:00:00Z') + i*86400000).toISOString().slice(0,10),
      contributionCount: [0,1,12,123][i%4],
      contributionLevel: ['NONE','FIRST_QUARTILE','SECOND_QUARTILE','FOURTH_QUARTILE'][i%4]
    }));
    const weeks = [];
    for (let i=0; i<days.length; i+=7) weeks.push({contributionDays: days.slice(i,i+7)});
    res.end(JSON.stringify({data:{user:{contributionsCollection:{contributionCalendar:{
      totalContributions: days.reduce((sum, day) => sum+day.contributionCount,0), weeks
    }}}}}));
  });
}).listen(process.env.PORT);
