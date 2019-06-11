import Vue from 'vue';
import Router from 'vue-router';
import Instruments from './components/Instruments.vue';

Vue.use(Router);

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/instruments',
      name: 'Instruments',
      component: Instruments,
    }
  ],
});
