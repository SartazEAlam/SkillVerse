import { createBrowserRouter } from 'react-router-dom'
import { Shell } from '../components/layout/Shell'
import { DashboardPage } from '../pages/DashboardPage'
import { ExplorePage } from '../pages/ExplorePage'
import { SkillsPage } from '../pages/SkillsPage'
import { CourseOverviewPage } from '../pages/CourseOverviewPage'
import { LoginPage } from '../pages/LoginPage'
import { RegisterPage } from '../pages/RegisterPage'
import { ProfilePage } from '../pages/ProfilePage'
import { NotFoundPage } from '../pages/NotFoundPage'
import { LessonWorkspacePage } from '../pages/LessonWorkspacePage'
import { CreatorStudioPage } from '../pages/CreatorStudioPage'
import { CourseEditorPage } from '../pages/CourseEditorPage'
import { ProjectsPage } from '../pages/ProjectsPage'
import { ProjectDetailPage } from '../pages/ProjectDetailPage'
import { SubmissionWorkspacePage } from '../pages/SubmissionWorkspacePage'
import { PortfolioManagementPage } from '../pages/PortfolioManagementPage'
import { PublicPortfolioPage } from '../pages/PublicPortfolioPage'

export const router = createBrowserRouter([
  {
    path: '/creator/courses/:courseId/preview/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/creator/courses/:courseId/preview',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/creator/courses/:courseId',
    element: <CourseEditorPage />,
  },
  {
    path: '/learn/:courseSlug/:moduleSlug/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/learn/:courseSlug/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/learn/:courseSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/courses/:courseSlug/learn/:lessonSlug',
    element: <LessonWorkspacePage />,
  },
  {
    path: '/',
    element: <Shell />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'explore',
        element: <ExplorePage />,
      },
      {
        path: 'skills',
        element: <SkillsPage />,
      },
      {
        path: 'projects',
        element: <ProjectsPage />,
      },
      {
        path: 'projects/:slugOrId',
        element: <ProjectDetailPage />,
      },
      {
        path: 'submissions/:submissionId',
        element: <SubmissionWorkspacePage />,
      },
      {
        path: 'portfolio',
        element: <PortfolioManagementPage />,
      },
      {
        path: 'portfolio/:slugOrId',
        element: <PublicPortfolioPage />,
      },
      {
        path: 'u/:slugOrId/portfolio',
        element: <PublicPortfolioPage />,
      },
      {
        path: 'creator',
        element: <CreatorStudioPage />,
      },
      {
        path: 'courses/:slug',
        element: <CourseOverviewPage />,
      },
      {
        path: 'login',
        element: <LoginPage />,
      },
      {
        path: 'register',
        element: <RegisterPage />,
      },
      {
        path: 'profile',
        element: <ProfilePage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
