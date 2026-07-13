/* digib00age UI-kit — fake catalogue data (no real cover art / copyright). */
(function () {
  const C = 'assets/covers/';
  const ITEMS = [
    { id: 'tron', title: 'Tron: Download', year: 2025, type: 'single', cover: C+'tron-download.png', pages: 353, genres:['Sci-Fi','Adventure'], publisher:'Marvel', writer:'Mateus Manhanini', summary:'In the digital frontier of the Grid, a program races to deliver a payload before the system purges it forever.', state:'unread', favourite:false },
    { id: 'w0rld', title: 'w0rldtr33', year: 2026, type: 'series', cover: C+'w0rldtr33.png', issues: 20, genres:['Horror','Thriller'], publisher:'Image', writer:'James Tynion IV', summary:'A hidden layer of the early internet — the Undernet — holds something that should never have been found.', state:'progress', progress:65, unreadCount:7, favourite:true },
    { id: 'hello', title: 'Hello Darkness', year: 2026, type: 'series', cover: C+'hello-darkness.png', issues: 22, genres:['Horror','Anthology'], publisher:'BOOM! Studios', writer:'Various', summary:'An ongoing horror anthology where every door opens onto a worse room than the last.', state:'unread', unreadCount:22, favourite:false },
    { id: 'mega', title: 'Megatropolis', year: 2021, type: 'single', cover: C+'megatropolis.png', pages: 98, genres:['Crime','Sci-Fi'], publisher:'2000 AD', writer:'Kenneth Niemand', summary:'A reimagined art-deco metropolis where the line between law and order has been painted over.', state:'read', favourite:false },
    { id: 'dredd', title: 'Judge Dredd: Emerald Isle', year: 2001, type: 'single', cover: C+'judge-dredd.png', pages: 76, genres:['Action','Sci-Fi'], publisher:'2000 AD', writer:'Garth Ennis', summary:'Dredd is dragged across the irradiated Atlantic to the lawless Emerald Isle.', state:'unread', favourite:false },
    { id: 'portraits', title: 'Portraits', year: 2023, type: 'single', cover: C+'portraits.png', pages: 118, genres:['Drama','Slice of Life'], publisher:'Self-Published', writer:'Nikos Tzouridkos', summary:'Quiet vignettes of a seaside town, drawn between commissions.', state:'unread', favourite:false },
    { id: 'faint', title: 'The Faint Of Heart', year: 2023, type: 'single', cover: C+'the-faint-of-heart.png', pages: 308, genres:['All-Ages','Adventure'], publisher:'Top Shelf', writer:'Kerilynn Wilson', summary:'In a town that surrendered its hearts for safety, one girl wants hers back.', state:'progress', progress:40, favourite:false },
    { id: 'blake', title: 'The Adventures of John Blake', year: 2017, type: 'single', cover: C+'john-blake.png', pages: 161, genres:['Adventure','Mystery'], publisher:'Scholastic', writer:'Philip Pullman', summary:'A boy lost in time aboard a ship that sails the fog between centuries.', state:'unread', favourite:false },
    { id: 'ruby', title: 'The Ruby Equation', year: 2015, type: 'single', cover: C+'the-ruby-equation.png', pages: 75, genres:['Romance','Comedy'], publisher:'Oni Press', writer:'Sarah Kuhn', summary:'A barista with a strict formula for human happiness meets a variable she cannot solve.', state:'read', favourite:true },
    { id: 'turn', title: 'Turncoat', year: 2017, type: 'single', cover: C+'turncoat.png', pages: 113, genres:['Sci-Fi','Noir'], publisher:'Boom! Studios', writer:'Alex Paknadel', summary:'After the alien occupation ends, a human collaborator turns private eye.', state:'unread', favourite:false },
    { id: 'bunnies', title: 'Itty Bitty Bunnies in Rainbow Pixie Candyland', year: 2016, type: 'single', cover: C+'itty-bitty-bunnies.png', pages: 79, genres:['Humour','All-Ages'], publisher:'Dynamite', writer:'Art Baltazar', summary:'It is exactly as sweet, and exactly as deranged, as the title promises.', state:'unread', favourite:false },
    { id: 'die', title: '1000 Ways To Die', year: 2011, type: 'single', cover: C+'1000-ways-to-die.png', pages: 219, genres:['Horror','Non-Fiction'], publisher:'Zenescope', writer:'Jim Campbell', summary:'Based on the hit series — a compelling look at the science of living, combined with the randomness of death.', state:'unread', favourite:false },
    { id: 'bone', title: 'Bone', year: 2004, type: 'series', cover: C+'bone.png', issues: 55, genres:['Fantasy','All-Ages'], publisher:'Cartoon Books', writer:'Jeff Smith', summary:'Three cousins, lost in an uncharted valley, are drawn into a sweeping fantasy epic.', state:'progress', progress:88, unreadCount:6, favourite:true },
    { id: 'scenes', title: '100 Scenes', year: 2010, type: 'single', cover: C+'100-scenes.png', pages: 106, genres:['Abstract','Art'], publisher:'Wider Screenings', writer:'Tim Gaze', summary:'One hundred abstract "scenes" created through decalcomania — a technique pioneered by surrealist Oscar Domínguez.', state:'unread', favourite:false },
    { id: 'blade', title: 'Blade Runner 2019', year: 2019, type: 'series', cover: C+'blade-runner-2019.png', issues: 12, genres:['Action','Adventure','Sci-Fi'], publisher:'Titan', writer:'Michael Green', summary:'In the new-noir Los Angeles of 2019, veteran Blade Runner Ash has a new case: a billionaire\u2019s missing child.', state:'unread', unreadCount:12, favourite:false },
    { id: 'weather', title: 'The Weather Man', year: 2018, type: 'single', cover: C+'the-weather-man.png', pages: 144, genres:['Sci-Fi','Thriller'], publisher:'Image', writer:'Jody LeHeup', summary:'On terraformed Mars, the solar system\u2019s most beloved weatherman is accused of the worst crime in history.', state:'unread', favourite:false },
    { id: 'saga', title: 'Saga', year: 2012, type: 'series', cover: C+'saga.png', issues: 66, genres:['Fantasy','Sci-Fi','Romance'], publisher:'Image', writer:'Brian K. Vaughan', summary:'Two soldiers from opposite sides of a galactic war flee with their newborn daughter.', state:'read', favourite:true },
    { id: 'nilson', title: 'The Adventures of Nilson Groundthumper', year: 2014, type: 'single', cover: C+'nilson-groundthumper.png', pages: 113, genres:['Humour','Fantasy'], publisher:'Fantagraphics', writer:'Stan Sakai', summary:'A wandering rabbit-knight and his hairy companion blunder through a feudal countryside.', state:'unread', favourite:false },
  ];

  ITEMS.forEach((it) => {
    it.metaLabel = it.type === 'series' ? `${it.issues} issues` : `${it.pages} pages`;
  });

  window.LIB = {
    items: ITEMS,
    byId: (id) => ITEMS.find((x) => x.id === id),
    strips: [
      { label: 'Recently Added', ids: ['tron','w0rld','hello','mega','dredd','blade','weather','saga'] },
      { label: 'Random Unread', ids: ['nilson','portraits','faint','blake','die','turn','bunnies','scenes'] },
      { label: 'Adventure', ids: ['blade','dredd','tron','blake','bone','nilson'] },
    ],
  };
})();
